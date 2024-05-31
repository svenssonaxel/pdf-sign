import random
from reportlab.lib.colors import Color, black
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from intmp import intmp
from typing import List

class Box:
    def __init__(self, x, y, w, h):
        assert w>0
        assert h>0
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    def clone(self):
        return Box(self.x, self.y, self.w, self.h)
    def split(self, vertical: bool, cut: float):
        box1 = self.clone()
        box2 = self.clone()
        if vertical:
            cut = int(cut*self.w)
            box1.w=cut
            box2.x+=cut
            box2.w-=cut
        else:
            cut = int(cut*self.h)
            box1.h=cut
            box2.y+=cut
            box2.h-=cut
        return (box1, box2)

class Rng:
    def __init__(self, seed):
        self.rng = random.Random()
        self.rng.seed(seed)
    def random(self): return self.rng.random()
    def chance(self, percent): return self.random() < (percent / 100.0)
    def float_in(self, a, b): return a + (b - a) * self.random()
    def int_in(self, a, b): return a + int((b - a) * self.random())
    def float_seq(self, n): return [self.random() for _ in range(n)]
    def split(self, n=2): return [Rng(seed) for seed in self.float_seq(n)]
    def color(self, alpha=None):
        r, g, b, a = [ self.random() for _ in range(4) ]
        return Color(r, g, b, alpha=(alpha or a))
    def split_box(self, box):
        return box.split(box.w>box.h, self.float_in(0.3, 0.7))
    def cartesian_sample(self, *lists):
        tot = max(len(x) for x in lists) * len(lists)
        res = []
        for l in lists:
            lenl = len(l)
            items = [l[x%lenl] for x in range(tot)]
            shuffled = items[:]
            self.rng.shuffle(shuffled)
            res.append(shuffled)
        return [*zip(*res)]

def draw_rect(c: Canvas, box: Box, fill_color: Color = black, stroke_color: Color | None = None, sw: float = 1.0):
    c.saveState()
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(sw)
    c.rect(box.x, box.y, box.w, box.h,
           fill=1, stroke=int(bool(stroke_color)))
    c.restoreState()

def draw_rnd_line(c: Canvas, *, seed: float = 0, box: Box, stroke_color: Color = black, sw: float = 1.0):
    c.saveState()
    c.setStrokeColor(stroke_color)
    c.setLineWidth(sw)
    rng = Rng(seed)
    x1 = rng.float_in(box.x, box.x+box.w)
    y1 = rng.float_in(box.y, box.y+box.h)
    x2 = rng.float_in(box.x, box.x+box.w)
    y2 = rng.float_in(box.y, box.y+box.h)
    c.line(x1, y1, x2, y2)
    c.restoreState()

def draw_label(c: Canvas, x: float, y: float, txt: str, size: int = 12):
    c.saveState()
    c.setFillColor(black)
    c.setFont("Times-Roman", size)
    c.drawString(x, y, txt)
    c.restoreState()

def draw_area(c: Canvas, seed: float, box: Box, depth: int = 10, txt: str = "Lorem ipsum", line_chance: int = 10, rect_chance: int = 5):
    rng = Rng(seed)
    c.saveState()
    p = c.beginPath()
    p.rect(box.x, box.y, box.w, box.h)
    c.clipPath(p, stroke=0, fill=0)
    # Base case
    if depth <= 0 or min(box.w, box.h) < 40:
        if rng.chance(50):
            draw_rect(c, box=box, fill_color=rng.color())
        else:
            draw_label(c,
                       x=box.x + 0.2*box.w, y=box.y + box.h/2,
                       txt=txt,
                       size=int(max(2, min(24, box.h/2, 5*box.w/len(txt)))))
        c.restoreState()
        return
    # Maybe paint a line or faint rect, then recurse into 2 children, then maybe
    # paint a line or faint rect
    if rng.chance(line_chance):
        draw_rnd_line(c, seed=rng.random(), box=box, sw=rng.float_in(1, 5))
    elif rng.chance(rect_chance):
        draw_rect(c, box=box, fill_color=rng.color())
    for sub_box in rng.split_box(box):
        draw_area(c, seed=rng.random(), box=sub_box, depth=depth+1, txt=txt,
                  line_chance=line_chance, rect_chance=rect_chance)
    if rng.chance(line_chance):
        draw_rnd_line(c, seed=rng.random(), box=box,
                      stroke_color=rng.color(), sw=rng.float_in(1, 5))
    elif rng.chance(rect_chance):
        draw_rect(c, box=box, fill_color=rng.color(alpha=0.1))
    c.restoreState()

class Paper:
    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h
    def draw(self, c: Canvas):
        raise NotImplementedError()

class Page(Paper):
    def __init__(self, seed: float, w: float, h: float, margin: float):
        super().__init__(w, h)
        self.seed = seed
        self.margin = margin
    def draw(self, c: Canvas):
        draw_area(c, seed=self.seed,
                  box=Box(self.margin, self.margin,
                          self.w - 2*self.margin, self.h - 2*self.margin))

class Signature(Paper):
    def __init__(self, seed: float = 0, w: float = 238, h: float = 170):
        super().__init__(w, h)
        self.seed = seed
    def draw(self, c: Canvas):
        draw_area(c, seed=self.seed,
                  txt="Sigtxt",
                  box=Box(0, 0, self.w, self.h),
                  line_chance=100,
                  rect_chance=0)

class Text(Paper):
    def __init__(self, text: str, size: float = 12):
        w = pdfmetrics.stringWidth(text, "Times-Roman", size) + 2
        h = 2 * size + 2
        super().__init__(w, h)
        self.text = text
        self.size = size
    def draw(self, c: Canvas):
        c.saveState()
        c.setFillColor(black)
        c.setFont("Times-Roman", self.size)
        c.drawString(1, self.size + 1, self.text)
        c.restoreState()

class TextField(Paper):
    def __init__(self, field_name: str, w: float = 119, h: float = 24):
        super().__init__(w, h)
        self.field_name = field_name
    def draw(self, c: Canvas):
        form = c.acroForm
        form.textfield(name=self.field_name, tooltip=self.field_name,
                       x=0, y=0, width=self.w, height=self.h,
                       borderColor=None, fillColor=None,
                       textColor=None, forceBorder=False)

class Empty(Paper):
    def draw(self, c: Canvas):
        pass

def gen_rnd_pages(seed=0, n=1, w=595, h=842, margin=10):
    rng = Rng(seed)
    return tuple(Page(seed=rng.random(), w=w, h=h, margin=margin)
                 for _ in range(n))

class Signed_page(Paper):
    def __init__(self, page: Paper, signature: Paper, cx: float, cy: float, r: float = 1):
        super().__init__(page.w, page.h)
        self.p = page
        self.sig = signature
        self.cx = cx
        self.cy = cy
        self.r = r
    def draw(self, c: Canvas):
        self.p.draw(c)
        c.saveState()
        c.translate(self.p.w*self.cx, self.p.h*(1 - self.cy))
        c.scale(self.r, self.r)
        c.translate(- self.sig.w*0.5, - self.sig.h*0.5)
        self.sig.draw(c)
        c.restoreState()

def sign_pages(pages: List[Paper], signature: Paper, idx: int, cx: float, cy: float, r: float = 1):
    if idx < 0: idx+=len(pages)
    assert 0 <= idx < len(pages)
    return [*pages[:idx],
            Signed_page(page=pages[idx], signature=signature, cx=cx, cy=cy, r=r),
            *pages[idx+1:]]

def gen_pdf(pages: List[Paper], description: str):
    assert len(pages)>0
    outfile = intmp('pdf', description)
    def pagesize(page: Paper): return (page.w, page.h)
    c = Canvas(str(outfile), pagesize=pagesize(pages[0]))
    for i, page in enumerate(pages):
        page.draw(c)
        if len(pages)-1>i and pagesize(page) != pagesize(pages[i+1]):
            c.setPageSize(pagesize(pages[i+1]))
        c.showPage()
    c.save()
    return outfile
