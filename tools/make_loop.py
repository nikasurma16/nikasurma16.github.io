# -*- coding: utf-8 -*-
"""
Turn the rendered frame sequence into a seamless loop and encode it for the web.

out[i] = S[i]                              for i in [C, L)
out[i] = lerp(S[L+i], S[i], i / C)         for i in [0, C)

so out[L-1] -> out[0] continues the source motion instead of cutting back.
"""
import os
import shutil
import subprocess

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "frames")
LOOP = os.path.join(HERE, "loop")
DST = r"C:\nika-sur-ma.github.io\assets\video"

START = 300      # skip the first 10 s while the simulation settles
L = 360          # 12 s at 30 fps
C = 60           # 2 s crossfade

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def build_frames():
    if os.path.isdir(LOOP):
        shutil.rmtree(LOOP)
    os.makedirs(LOOP)

    def src(i):
        return os.path.join(FRAMES, "f%05d.jpg" % (START + i + 1))

    for i in range(L):
        if i >= C:
            shutil.copyfile(src(i), os.path.join(LOOP, "l%04d.jpg" % i))
        else:
            a = Image.open(src(L + i)).convert("RGB")
            b = Image.open(src(i)).convert("RGB")
            w = i / float(C)
            Image.blend(a, b, w).save(os.path.join(LOOP, "l%04d.jpg" % i),
                                      "JPEG", quality=95)
    print("loop frames:", len(os.listdir(LOOP)))


def encode():
    os.makedirs(DST, exist_ok=True)
    seq = os.path.join(LOOP, "l%04d.jpg")

    mp4 = os.path.join(DST, "smoke.mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", "30", "-i", seq,
                    "-vf", "scale=1280:720",
                    "-c:v", "libx264", "-profile:v", "high", "-crf", "27",
                    "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-g", "60", "-movflags", "+faststart", "-an", mp4], check=True)

    webm = os.path.join(DST, "smoke.webm")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", "30", "-i", seq,
                    "-vf", "scale=1280:720",
                    "-c:v", "libvpx-vp9", "-crf", "38", "-b:v", "0",
                    "-row-mt", "1", "-cpu-used", "2", "-an", webm], check=True)

    poster = os.path.join(DST, "smoke-poster.jpg")
    Image.open(os.path.join(LOOP, "l0180.jpg")).convert("RGB").save(
        poster, "JPEG", quality=78, optimize=True, progressive=True)

    for p in (mp4, webm, poster):
        print(os.path.basename(p), os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    build_frames()
    encode()
