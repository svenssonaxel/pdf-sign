from util import runc, run1
from gen_pdf import Empty, gen_pdf
from intmp import intmp
from compare_pdf import assert_pdf_exactly_equal
from logging import info
from pathlib import Path

def test_pdf_create_empty():
    for [msg, *pos_args] in [
            ["unrecognized arguments: -Afoo", "-Afoo"],
            ["Invalid dimensions", "-d100"],
            ["Invalid dimensions", "-d10PTx100pt"],
            ["Invalid dimensions", "-d2.5.5cmx1in"],
            ["Invalid dimensions", "-d5cmxcm"],
            ["Invalid dimensions", "-d2A0"],
            ["Invalid dimensions", "-dLeggal"],
    ]:
        info(f"========== test_empty Begin case invalid: {pos_args}")
        empty_pdf = intmp('pdf', "Should not exist")
        err = run1(
            "pdf-create-empty",
            "-o", empty_pdf,
            *pos_args)
        assert not empty_pdf.exists()
        assert msg in err, f"Expected error message to contain {msg!r}, but got: {err}"
    _in = 72
    _mm = _in/25.4
    _cm = 10*_mm
    for [wpt, hpt, default_fname, *args] in [
            [3*_in, 2*_in, "empty-3inx2in.pdf"],
            [100, 36, "empty-100ptx36pts.pdf", "-d100ptx36pts"],
            [0.6789*_in, 2.3456*_cm, "empty-.6789inx2.3456cm.pdf", "-d.6789inx2.3456cm"],
            [3*_cm, 20*_mm, "empty-3cmx20mm.pdf", "-d3cmx20mm"],
            [841*_mm, 1189*_mm, "empty-A0.pdf", "-dA0"],
            [297*_mm, 210*_mm, "empty-a4L.pdf", "-da4L"],
            [31*_mm, 44*_mm, "empty-B10.pdf", "-dB10"],
            [229*_mm, 162*_mm, "empty-C5l.pdf", "-dC5l"],
            [8.5*_in, 14*_in, "empty-LeGaL.pdf", "-dLeGaL"],
            [11*_in, 8.5*_in, "empty-LettErL.pdf", "-dLettErL"],
    ]:
        info(f"========== test_empty Begin case {default_fname} = {pos_args}")
        wpt = round(wpt)
        hpt = round(hpt)
        expected_pdf = gen_pdf([Empty(w=wpt, h=hpt)], f"Empty {wpt}ptx{hpt}pt")
        actual_1_pdf = Path(default_fname)
        assert not actual_1_pdf.exists()
        runc("pdf-create-empty", *args)
        assert actual_1_pdf.exists()
        actual_2_pdf = intmp('pdf', f"Same as {default_fname}")
        assert not actual_2_pdf.exists()
        runc("pdf-create-empty", "-o", actual_2_pdf, *args)
        assert actual_2_pdf.exists()
        assert_pdf_exactly_equal(actual_1_pdf, actual_2_pdf)
        assert_pdf_exactly_equal(expected_pdf, actual_1_pdf)
