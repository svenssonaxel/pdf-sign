from util import run1
from gen_pdf import Signature, gen_rnd_pages, gen_pdf
from intmp import intmp
from pathlib import Path

def test_pdf_sign():
    doc_pdf = gen_pdf(gen_rnd_pages(), f"Generated document")
    sig_pdf = gen_pdf([Signature(seed=0)], f"Generated signature")
    def test(*pos_args):
        doc_pdf_signed = intmp('pdf', f"Should not exist")
        err = run1("pdf-sign",
                   "-b", "-s", sig_pdf,
                   *pos_args,
                   "-o", doc_pdf_signed,
                   doc_pdf)
        assert not doc_pdf_signed.exists()
        assert "Requires python 3.7 or later" in err
    test("-x53%")
    test("-x53")
    test("-xL+53%")
    test("-xL+53")
    test("-xR-47%")
    test("-xR-47")
    test("-y80%")
    test("-y80")
    test("-yT+80%")
    test("-yT+80")
    test("-yB-20%")
    test("-yB-20")

def test_pdf_create_empty():
    def test(filename, *pos_args):
        err = run1("pdf-create-empty", *pos_args)
        assert not Path(filename).exists()
        assert "Requires python 3.7 or later" in err
    test("empty-3inx2in.pdf")
    test("empty-3inx2in.pdf", "-h")
    test("empty-3inx2in.pdf", "--help")
    test("file.pdf", "-o", "file.pdf")
    test("file.pdf", "--output", "file.pdf")
    test("file.pdf", "--output", "file.pdf")
    test("empty-4inx4in.pdf", "-d", "4inx4in")
    test("empty-3inx2in.pdf", "--invalid-option")

def test_pdf_from_text():
    def test(*pos_args):
        filename = "file.pdf"
        err = run1("pdf-from-text", "-o", filename, *pos_args)
        assert not Path(filename).exists()
        assert "Requires python 3.7 or later" in err
    test("-t", "abc")
    test("-t", "abc", "-s20")
    test("-t", "abc", "-m1cm")
    test("-t", "abc", "-b")
