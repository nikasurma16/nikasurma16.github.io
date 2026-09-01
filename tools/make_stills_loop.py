# -*- coding: utf-8 -*-
"""
Build a background loop out of still photographs.

    python tools/make_stills_loop.py <name> <a.jpg> <b.jpg> [...]

The photographs are turned monochrome and cross-dissolved into one another
on a cosine, so the sequence arrives back exactly where it started and the
repeat is invisible. Each frame also breathes on the same cosine, which
returns to its own starting scale for the same reason.

Writes assets/video/<name>.mp4 and <name>-poster.jpg.
"""
import math
import os
import shutil
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageEnhance, ImageOps

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "assets", "video")

WIDTH, HEIGHT = 1280, 720
FPS = 25
SECONDS_PER_IMAGE = 8.0
ZOOM = 0.06          # how far each photograph breathes
CONTRAST = 1.12
ROTATE = True        # upside down


def prepare(path):
    """Monochrome, contrast-lifted, cropped to fill the frame with room to zoom."""
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("L")
    if ROTATE:
        im = im.rotate(180)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    big = (int(WIDTH * (1 + ZOOM * 2)), int(HEIGHT * (1 + ZOOM * 2)))
    return ImageOps.fit(im, big, Image.LANCZOS, centering=(0.5, 0.5)).convert("RGB")


def framed(src, zoom):
    """Crop the working image down to output size at the given zoom."""
    w = int(WIDTH * (1 + ZOOM * 2) / (1 + zoom))
    h = int(HEIGHT * (1 + ZOOM * 2) / (1 + zoom))
    x = (src.width - w) // 2
    y = (src.height - h) // 2
    return src.crop((x, y, x + w, y + h)).resize((WIDTH, HEIGHT), Image.LANCZOS)


def main():
    global ROTATE
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--upright" in sys.argv[1:]:
        ROTATE = False
    if len(args) < 3:
        print(__doc__)
        return 1
    name, paths = args[0], args[1:]

    plates = [prepare(p) for p in paths]
    n = len(plates)
    total = int(round(SECONDS_PER_IMAGE * n * FPS))

    work = os.path.join(ROOT, "tools", "_frames_" + name)
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)

    for i in range(total):
        pos = (i / float(total)) * n          # 0 .. n, wraps to 0
        k = int(math.floor(pos)) % n
        f = pos - math.floor(pos)
        # ease the dissolve so neither end of it has a visible corner
        w = (1 - math.cos(math.pi * f)) / 2

        za = ZOOM * (1 - math.cos(2 * math.pi * (pos / n))) / 2
        zb = ZOOM - za

        a = framed(plates[k], za)
        b = framed(plates[(k + 1) % n], zb)
        Image.blend(a, b, w).save(os.path.join(work, "f%05d.jpg" % i),
                                  "JPEG", quality=92)

    os.makedirs(DST, exist_ok=True)
    mp4 = os.path.join(DST, name + ".mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error",
                    "-framerate", str(FPS), "-i", os.path.join(work, "f%05d.jpg"),
                    "-c:v", "libx264", "-profile:v", "high", "-crf", "27",
                    "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-g", str(FPS * 2), "-movflags", "+faststart", "-an", mp4],
                   check=True)

    poster = os.path.join(DST, name + "-poster.jpg")
    Image.open(os.path.join(work, "f00000.jpg")).save(
        poster, "JPEG", quality=76, optimize=True, progressive=True)

    shutil.rmtree(work)
    for p in (mp4, poster):
        print(os.path.basename(p), os.path.getsize(p) // 1024, "KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
