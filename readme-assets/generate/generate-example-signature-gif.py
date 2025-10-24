from pathlib import Path
from os import environ
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from subprocess import run
from pypdf import PdfReader

out = Path(environ["out"])
src = Path(environ["src"])

sig_in = src / "example-signature.pdf"
page0 = PdfReader(str(sig_in)).pages[0]
box = getattr(page0, "cropbox", None) or page0.mediabox
width, height = float(box.width), float(box.height)

red = Color(1, 0, 0)
lw = min(width, height) * 0.02
hlw = lw / 2.0

c = canvas.Canvas("frame-and-cursor.pdf", pagesize=(width, height))
c.setStrokeColor(red)
c.setLineWidth(lw)
c.setLineCap(1) # round
c.rect(0, 0, width, height, fill=0, stroke=1)
c.translate(width / 2.0, height / 2.0)
c.rotate(15)
scale = min(width, height) * 0.01
def scale_pt(p):
    x, y = p
    return (scale*x, scale*y)
def mirror_pt(p):
    x, y = p
    return (-x, y)
def line(p1, p2):
    x1, y1 = p1; x2, y2 = p2
    c.line(x1, y1,  x2, y2)
def scaled_and_mirrored_polyline(p1, p2, *pn):
    sp1 = scale_pt(p1); sp2 = scale_pt(p2)
    line(sp1, sp2)
    msp1 = mirror_pt(sp1); msp2 = mirror_pt(sp2)
    line(msp1, msp2)
    if pn: scaled_and_mirrored_polyline(p2, *pn)
scaled_and_mirrored_polyline(
    ( 0,   0),
    (10, -17),
    ( 3, -15),
    ( 3, -28),
    ( 0, -28))
c.showPage()
c.save()
def runc(*cmd):
    cmd = [str(x) for x in cmd]
    print(" ".join(cmd))
    run(cmd, check=True)
runc("pdf-sign", "-b", "--continue-on-warnings",
     "-s", "frame-and-cursor.pdf",
     "-o", "example-signature-gif.pdf",
     "-W100%", "-H100%", "-y50%",
     src / "example-signature.pdf")
runc("magick",
     "-density", "600",
     "example-signature-gif.pdf",
     "-background", "white",
     "-alpha", "remove",
     "-alpha", "off",
     out / "example-signature.gif")
