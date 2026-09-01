# -*- coding: utf-8 -*-
"""
Take the Smoke and Liquid Displacement .toe, expand it, inject an Execute DAT
that writes every frame of /project1/comp4 to disk and then quits, and collapse
it back into a runnable .toe.
"""
import os
import shutil
import struct
import subprocess
import sys

BIN = r"C:\Program Files\Derivative\TouchDesigner\bin"
SRC = r"C:\touchdesigner\tox[toe\Project file - Smoke and Liquid Displacement Effects.2.toe"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "render")
FRAMES = os.path.join(HERE, "frames")
N_FRAMES = 900                      # 30 s at 30 fps

CALLBACKS = '''# injected: offline render of /project1/comp4
import os

OUT = r"{frames}"
N = {n}
LOG = os.path.join(OUT, "_log.txt")


def log(m):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(str(m) + "\\n")
    except Exception:
        pass


def onStart():
    try:
        os.makedirs(OUT, exist_ok=True)
    except Exception:
        pass
    log("onStart build=%s" % app.build)
    t = op("/project1/comp4")
    log("comp4=%s res=%s" % (t, (t.width, t.height) if t else None))
    return


def onCreate():
    log("onCreate")
    return


def onFrameStart(frame):
    return


count = [0]


def onFrameEnd(frame):
    # The timeline loops, so count our own frames instead of trusting the
    # timeline number - otherwise a second pass overwrites the first.
    count[0] += 1
    i = count[0]
    if i == 1:
        log("first frame end")
    if i <= N:
        try:
            op("/project1/comp4").save(os.path.join(OUT, "f%05d.jpg" % i), quality=0.95)
        except Exception as e:
            log("save %d failed: %s" % (i, e))
    else:
        log("done at %d" % i)
        try:
            project.quit(force=True)
        except Exception as e:
            log("quit failed: %s" % e)
    return


def onPlayStateChange(state):
    return


def onDeviceChange():
    return


def onProjectPreSave():
    return


def onProjectPostSave():
    return
'''


def dat_text_blob(text):
    """The .text payload format used by expanded .toe files."""
    body = text.encode("utf-8")
    return (b"2\n*"
            + struct.pack(">5i", 1, 1, 1, 1, 2)
            + struct.pack(">i", len(body))
            + body)


def run(*args):
    p = subprocess.run(args, capture_output=True, text=True, cwd=WORK)
    print(" ".join(os.path.basename(a) for a in args[:1]), "->", p.returncode)
    if p.stdout.strip():
        print("   ", p.stdout.strip())
    if p.stderr.strip():
        print("   !", p.stderr.strip())
    return p.returncode


def main():
    if os.path.isdir(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    toe = os.path.join(WORK, "smoke.toe")
    shutil.copy2(SRC, toe)

    run(os.path.join(BIN, "toeexpand.exe"), "smoke.toe")

    d = os.path.join(WORK, "smoke.toe.dir")
    if not os.path.isdir(d):
        print("expand failed")
        return 1

    # Non-realtime so every frame is rendered rather than dropped.
    start = os.path.join(d, ".start")
    s = open(start, encoding="utf-8").read().replace("realtime on", "realtime off")
    open(start, "w", encoding="utf-8", newline="\n").write(s)

    base = os.path.join(d, "project1", "tdrender")
    open(base + ".n", "w", encoding="utf-8", newline="\n").write(
        "DAT:execute\n"
        "tile 2875 200 160 130\n"
        "flags =  parlanguage 0\n"
        "color 0.55 0.55 0.55 \n"
        "end\n")
    open(base + ".parm", "w", encoding="utf-8", newline="\n").write(
        "?\n"
        "active 0 on\n"
        "start 0 on\n"
        "create 0 on\n"
        "frameend 0 on\n"
        "?\n")
    with open(base + ".text", "wb") as f:
        f.write(dat_text_blob(CALLBACKS.format(frames=FRAMES, n=N_FRAMES)))

    # The table of contents is the file list toecollapse walks, so the new
    # node has to be listed in it too, right after the operator it renders.
    toc = os.path.join(WORK, "smoke.toe.toc")
    lines = open(toc, encoding="utf-8").read().splitlines()
    anchor = lines.index("project1/comp4.parm") + 1
    lines[anchor:anchor] = ["project1/tdrender.n",
                            "project1/tdrender.parm",
                            "project1/tdrender.text"]
    open(os.path.join(WORK, "smoke_render.toe.toc"), "w",
         encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")

    out = os.path.join(WORK, "smoke_render.toe")
    if os.path.exists(out):
        os.remove(out)
    shutil.move(toe, os.path.join(WORK, "orig.toe"))
    os.rename(os.path.join(WORK, "smoke.toe.dir"), os.path.join(WORK, "smoke_render.toe.dir"))
    run(os.path.join(BIN, "toecollapse.exe"), "smoke_render.toe.dir")

    if os.path.exists(out):
        print("built", out, os.path.getsize(out), "bytes")
        return 0
    print("collapse produced nothing; dir contents:", os.listdir(WORK))
    return 1


if __name__ == "__main__":
    sys.exit(main())
