# -*- coding: utf-8 -*-
"""
Build the about-page background out of a short clip: upscale, blur it into a
soft field, and make it a boomerang so it loops without a cut.

The source fades from light to dark across its length, so a straight loop
would pop. Playing it forward and then backwards removes the seam entirely.
"""
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\sur_ma\Downloads\Telegram Desktop\photo_2026-09-01_10-39-30.mp4"
DST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "video")

SIZE = 1440        # 3x the 480x480 source
SIGMA = 20         # blur radius at that size
NAME = "portrait"

CHAIN = ("scale={s}:{s}:flags=lanczos,"
         "gblur=sigma={g}:steps=3,"
         "format=yuv420p".format(s=SIZE, g=SIGMA))

BOOMERANG = ("[0:v]" + CHAIN + ",split[a][b];"
             "[b]reverse[r];"
             "[a][r]concat=n=2:v=1:a=0[v]")


def main():
    os.makedirs(DST, exist_ok=True)

    mp4 = os.path.join(DST, NAME + ".mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", SRC,
                    "-filter_complex", BOOMERANG, "-map", "[v]",
                    "-c:v", "libx264", "-profile:v", "high", "-crf", "28",
                    "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-g", "60", "-movflags", "+faststart", "-an", mp4], check=True)

    webm = os.path.join(DST, NAME + ".webm")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", SRC,
                    "-filter_complex", BOOMERANG, "-map", "[v]",
                    "-c:v", "libvpx-vp9", "-crf", "40", "-b:v", "0",
                    "-row-mt", "1", "-cpu-used", "2", "-an", webm], check=True)

    still = os.path.join(DST, "_tmp_poster.png")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", "1", "-i", SRC,
                    "-frames:v", "1", "-vf", CHAIN, still], check=True)
    poster = os.path.join(DST, NAME + "-poster.jpg")
    Image.open(still).convert("RGB").save(poster, "JPEG", quality=76,
                                          optimize=True, progressive=True)
    os.remove(still)

    for p in (mp4, webm, poster):
        print(os.path.basename(p), os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main()
