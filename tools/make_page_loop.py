# -*- coding: utf-8 -*-
"""
Cut a seamless background loop out of a long clip.

    python tools/make_page_loop.py <source.mp4> <name> <start_seconds> [length]
                                   [--upright] [--gray]

The loop opens on a crossfade between its own tail and its own head, so the
repeat has no cut:

    out[0..C]  = crossfade(src[L..L+C], src[0..C])
    out[C..L]  = src[C..L]

Writes assets/video/<name>.mp4, .webm and <name>-poster.jpg.
"""
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
DST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "video")

WIDTH, HEIGHT, FPS = 960, 540, 30
CROSSFADE = 2.0
ROTATE = True      # upside down; pass --upright to keep it the right way up
GRAY = False       # pass --gray for monochrome


def chain(src, start, length):
    c = CROSSFADE
    look = ("hflip,vflip," if ROTATE else "") + ("hue=s=0," if GRAY else "")
    return (
        "[0:v]trim=start={s}:duration={total},setpts=PTS-STARTPTS,"
        "fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,"
        "crop={w}:{h},{r}hqdn3d=3:3:6:6,format=yuv420p,split[a][b];"
        # xfade insists on a constant frame rate, which trim/setpts loses.
        "[a]trim=duration={L},setpts=PTS-STARTPTS,fps={fps},settb=AVTB[head];"
        "[b]trim=start={L}:duration={c},setpts=PTS-STARTPTS,fps={fps},settb=AVTB[tail];"
        "[tail][head]xfade=transition=fade:duration={c}:offset=0[v]"
    ).format(s=start, total=length + c, L=length, c=c,
             fps=FPS, w=WIDTH, h=HEIGHT, r=look)


def main():
    global ROTATE, GRAY
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if "--upright" in flags:
        ROTATE = False
    if "--gray" in flags:
        GRAY = True

    if len(args) < 3:
        print(__doc__)
        return 1
    src, name, start = args[0], args[1], float(args[2])
    length = float(args[3]) if len(args) > 3 else 16.0

    os.makedirs(DST, exist_ok=True)
    filt = chain(src, start, length)

    mp4 = os.path.join(DST, name + ".mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src,
                    "-filter_complex", filt, "-map", "[v]",
                    "-c:v", "libx264", "-profile:v", "high", "-crf", "31",
                    "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-g", "60", "-movflags", "+faststart", "-an", mp4], check=True)

    webm = os.path.join(DST, name + ".webm")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src,
                    "-filter_complex", filt, "-map", "[v]",
                    "-c:v", "libvpx-vp9", "-crf", "46", "-b:v", "0",
                    "-row-mt", "1", "-cpu-used", "2", "-an", webm], check=True)

    still = os.path.join(DST, "_tmp_" + name + ".png")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error",
                    "-ss", str(start + length / 2), "-i", src, "-frames:v", "1",
                    "-vf", "scale={w}:{h}:force_original_aspect_ratio=increase,"
                           "crop={w}:{h},{r}null".format(
                               w=WIDTH, h=HEIGHT,
                               r=("hflip,vflip," if ROTATE else "")
                                 + ("hue=s=0," if GRAY else "")),
                    still], check=True)
    poster = os.path.join(DST, name + "-poster.jpg")
    Image.open(still).convert("RGB").save(poster, "JPEG", quality=76,
                                          optimize=True, progressive=True)
    os.remove(still)

    for p in (mp4, webm, poster):
        print(os.path.basename(p), os.path.getsize(p) // 1024, "KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
