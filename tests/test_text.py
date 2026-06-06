from util import runc, run1
from intmp import intmp
from gen_pdf import Text, Empty, sign_pages, gen_pdf
from pathlib import Path
from compare_pdf import assert_pdf_almost_equal, assert_pdf_exactly_equal
from logging import info

def test_pdf_from_text():
    for [msg, *pos_args] in [
            ["required: -t/--text", "-Afoo"],
            ["unrecognized arguments: -Afoo", "-tabcde", "-Afoo"],
    ]:
        err = run1("pdf-from-text", "-o", "nonexistent.pdf", *pos_args)
        assert not Path("nonexistent.pdf").exists()
        assert msg in err
    for [w, h, size, cx, cy, text, *pos_args] in [
            [30, 19, 12, 0.5, 0.5, "abcde", "-b"],
            [30, 11, 12, 0.5, 0.86, "abcde"],
            [34, 22, 14, 0.5, 0.5, "abcde", "-bs14"],
            [34, 12, 14, 0.5, 0.86, "abcde", "-s14"],
            [28, 17, 12, 0.5, 0.5, "abcde", "-b", "-m0"],
            [28,  9, 12, 0.5, 0.95, "abcde", "-m0"],
            [32, 20, 14, 0.5, 0.5, "abcde", "-bs14", "-m0"],
            [32, 10, 14, 0.5, 0.95, "abcde", "-s14", "-m0"],
            [38, 27, 12, 0.5, 0.5, "abcde", "-b", "-m5"],
            [38, 19, 12, 0.5, 0.72, "abcde", "-m5"],
            [42, 30, 14, 0.5, 0.5, "abcde", "-bs14", "-m5"],
            [42, 20, 14, 0.5, 0.72, "abcde", "-s14", "-m5"],
    ]:
        info(f"========== test_text Begin case: -t {text} {' '.join(pos_args)}")
        empty = Empty(w=w, h=h)
        txt = Text(text=text, size=size)
        adjusted = sign_pages(pages=[empty], signature=txt, idx=0, cx=cx, cy=cy, r=1)
        txt_expected_pdf = gen_pdf(adjusted, f"Generated '{text}' {size}pt pdf with reportlab")
        txt_actual_pdf = intmp('pdf', f"Created with pdf-from-text -t {text} {' '.join(pos_args)}")
        runc("pdf-from-text", "-o", txt_actual_pdf, "-t", text, *pos_args)
        assert_pdf_exactly_equal(txt_expected_pdf, txt_actual_pdf)
