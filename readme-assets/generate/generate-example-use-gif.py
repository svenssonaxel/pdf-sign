from pathlib import Path
from os import environ
from subprocess import run, Popen, PIPE
from time import sleep

OUT = Path(environ['out'])
TMP = Path(environ['TMPDIR'])
WIN_WIDTH = int(environ["WIN_WIDTH"])
WIN_HEIGHT = int(environ["WIN_HEIGHT"])

def runc(*cmd):
    cmd = [str(x) for x in cmd]
    print(" ".join(cmd))
    proc = run(cmd, capture_output=True, text=True, check=True)
    return proc.stdout, proc.stderr

def xdo(args, dur=0, slp=0.1):
    out, err = runc("xdotool", *args)
    assert err == "", f"xdotool error: {err}"
    assert out == "", f"xdotool output: {out}"
    if slp: sleep(slp)
    if dur: frame(dur)

def maximize_and_focus(win_class, dur, slp=3):
    xdo(["search", "--sync",
         "--onlyvisible", "--class", win_class,
         "windowmove", "0", "0",
         "windowsize", WIN_WIDTH, WIN_HEIGHT,
         "windowfocus"],
        dur=dur, slp=slp)

gifcmd = ["convert"]
frame_count = 0
def frame(dur=20):
    global frame_count, gifcmd
    frame_count += 1
    path = TMP / f"frame-{frame_count}.png"
    runc("magick", "import", "-window", "root",
         "-depth", 8, # bits per channel
         path)
    gifcmd += ["-delay", dur, path]

def press(key, dur=20, slp=None):
    if slp is None:
        if key == "Tab": slp = 1
        else: slp = 0.1
    xdo(["key", key], dur=dur, slp=slp)

def slowtype(chars, dur=20, slp=0.1):
    for char in chars:
        xdo(["key", "minus"] if char=="-" else ["type", char],
            dur=dur, slp=slp)

def dpi(r):
    runc("xrandr", "--dpi", r)

# Open terminal
st_proc = Popen(
    ["st", "-e",
     environ['BASHINTERACTIVE'],
     "--rcfile", environ['BASHRC'], "-i"],
    stdout=PIPE, stderr=PIPE,
    text=True,
)
maximize_and_focus("st", None)
press("XF86ZoomIn", None)
press("XF86ZoomIn", None)
press("XF86ZoomIn", None)
press("XF86ZoomIn", 200, 1)

# File listings
slowtype("ls -A")
press("Return", 200)
slowtype("ls -A .p")
press("Tab")
press("Return", 200)

# Open evince to show document then close
dpi(99)
slowtype("evi")
press("Tab")
slowtype(" ᛉ")
press("Tab", 150)
press("Return", None)
maximize_and_focus("evince", 300)
press("Ctrl+w", None)
maximize_and_focus("st", 150, 1)

# Open pdf-sign
dpi(162)
slowtype("pdf-s")
press("Tab")
slowtype("ᛉ")
press("Tab", 200)
press("Return", None)
maximize_and_focus("pdf-sign", 300, slp=3)

# Banish pointer (will otherwise interfere with menus)
xdo(["mousemove", WIN_WIDTH, WIN_HEIGHT],
    None)

# Select signature option 2
press("Alt+i", slp=1)
press("Down", slp=1)
press("Down", slp=1)
press("Down", 200, slp=1)
press("Return", 200, slp=3)

# Place signature
xdo(["mousemove", 0.63*WIN_WIDTH, 0.81*WIN_HEIGHT,
     "click", "1"],
    100, 3)

# Enlarge
press("Alt+i", slp=1)
press("Down", slp=1)
press("Down", slp=1)
press("Down", slp=1)
press("Down", slp=1)
press("Down", 150, slp=1)
press("Return", slp=3)
press("plus", slp=3)
press("plus", 100, slp=3)

# Sign and close
press("Alt+f", 200, slp=1)
press("Return", None)
maximize_and_focus("st", 200, 1)

# List files
slowtype("ls -A")
press("Return", 100)

# Open evince to show signed document then close
dpi(99)
slowtype("evi")
press("Tab")
slowtype(" ᛉ")
press("Tab")
press("s")
press("Tab", 100)
press("Return", None)
maximize_and_focus("evince", 500, slp=3)
press("Ctrl+w", None)
maximize_and_focus("st", 300, 1)

# Exit terminal without producing frames
press("Ctrl+d", None)
st_proc.wait(timeout=1)
assert st_proc.returncode == 0

# Process frames into animated gif
gifcmd += [ TMP / "output.gif" ]
runc(*gifcmd)
runc("gifsicle", "--optimize=3", "--no-extensions", "-k", "32",
     TMP / "output.gif", "-o", OUT / "example-use.gif")
