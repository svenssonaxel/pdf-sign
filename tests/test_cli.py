# CLI tests.
# - Generate PDF documents/signatures.
# - Sign them in various ways using batch pdf-sign.
# - Generate PDF files representing the expected result of signing.
# - Compare the resulting PDFs using approximate visual equality.
# These tests are meant to test both the CLI interface and the correctness of
# the output.

from util import m, runc, run1
from gen_pdf import Signature, Text, TextField, Empty, gen_rnd_pages, sign_pages, gen_pdf, Rng
from intmp import intmp
from compare_pdf import assert_pdf_almost_equal, assert_pdf_exactly_equal
from functools import cache
from logging import info
from pypdf import PdfReader, PdfWriter
from pathlib import Path

# helpers
def da(kw_1, **kw_2): return {**kw_1, **kw_2}
@cache
def expected(document, document_pdf, signature, signature_pdf, signature_index, x_coordinate, y_coordinate, resize_factor):
    doc_signed = sign_pages(pages=document, signature=signature, idx=signature_index, cx=x_coordinate, cy=y_coordinate, r=resize_factor)
    doc_signed_pdf = gen_pdf(doc_signed, f"{document_pdf.name} signed with {signature_pdf.name} at {(x_coordinate, y_coordinate)}*{resize_factor} before generation")
    return doc_signed_pdf
@cache
def actual(document_pdf, signature_pdf, pos_args):
    document_pdf_signed = intmp('pdf', f"{document_pdf.name} signed with {signature_pdf.name} using pdf-sign ... {' '.join(map(str, pos_args))} ...")
    runc("pdf-sign",
         "-b",
         *pos_args,
         "-o", document_pdf_signed,
         document_pdf)
    return document_pdf_signed
def good(document, document_pdf, signature, signature_pdf, signature_index, x_coordinate, y_coordinate, resize_factor, pos_args, diff_pages = []):
    assert_pdf_almost_equal(
        expected(document=document,
                 document_pdf=document_pdf,
                 signature=signature,
                 signature_pdf=signature_pdf,
                 signature_index=signature_index,
                 x_coordinate=x_coordinate,
                 y_coordinate=y_coordinate,
                 resize_factor=resize_factor),
        actual(document_pdf=document_pdf,
               signature_pdf=signature_pdf,
               pos_args=tuple(pos_args)),
        diff_pages)
def diff(diff_pages, **kw):
    assert "diff_pages" not in kw
    assert diff_pages
    return good(**da(kw, diff_pages = diff_pages))
def error(document_pdf, msg, pos_args):
    document_pdf_signed = intmp('pdf', "Should not exist")
    err = run1(
        "pdf-sign",
        "-b",
        *pos_args,
        "-o", document_pdf_signed,
        document_pdf)
    assert not document_pdf_signed.exists()
    assert msg in err, f"Expected error message to contain {msg!r}, but got: {err}"

# -p, -x, -y
def test_cli_position():
    rng = Rng(seed=0)
    doc_page_count = 2
    doc = gen_rnd_pages(seed=rng.random(), n=doc_page_count)
    doc_w = doc[0].w
    doc_h = doc[0].h
    sig = Signature(seed=rng.random())
    doc_pdf = gen_pdf(doc, f"Generated document with {doc_page_count} pages, {doc_w}x{doc_h} pt")
    sig_pdf = gen_pdf([sig], f"Generated signature, {sig.w}x{sig.h} pt")
    for [msg, *args] in [
            ["Invalid -x option", "-x53"],
            ["Invalid -x option", "-xL+53"],
            ["Invalid -x option", "-xR-47"],
            ["Invalid -y option", "-y80"],
            ["Invalid -y option", "-yT+80"],
            ["Invalid -y option", "-yB-20"],
            ["Invalid -x option", "-xT+10%"],
            ["Invalid -x option", "-xB-10%"],
            ["Invalid -y option", "-yL+10%"],
            ["Invalid -y option", "-yR-10%"],
            ["Invalid -x option", "-xC+2"],
            ["Invalid -x option", "-xC+cm"],
            ["Invalid -x option", "-xC+"],
            ["Invalid -x option", "-xC2cm"],
            ["Invalid -x option", "-xC2"],
            ["Invalid -x option", "-xCcm"],
            ["Invalid -x option", "-x+2cm"],
            ["Invalid -x option", "-x-2cm"],
            ["Invalid -x option", "-x+2"],
            ["Invalid -x option", "-x+cm"],
            ["Invalid -x option", "-x+"],
            ["Invalid -x option", "-x2"],
            ["Invalid -x option", "-xcm"],
            ["argument -x/--x-coordinate: expected one argument", "-x"],
            ["Page number out of range", "-p0"],
            ["Page number out of range", "-p3"],
            ["Page number out of range", "-p-3"],
    ]:
        error(document_pdf = doc_pdf, msg=msg, pos_args=["-s", sig_pdf, *args])
    for [[x_val, *x_args], [y_val, *y_args], [p_idx, *p_args]] in rng.cartesian_sample(
            [
                [0.5],
                [0.53, "-xC+3%"],
                [0.53, "--x-coordinate", f"C+{doc_w*0.03*2.54/72}cm"],
                [0.53, "-xL+53%"],
                [0.53, "-x", "R-47%"],
            ],
            [
                [0.75],
                [0.80, "-y80%"],
                [0.80, "--y-coordinate", "C+30%"],
                [0.80, f"-yT+{doc_h*0.8/72}in"],
                [0.80, "-y", "B-20%"],
            ],
            [
                [1],
                [0, "-p-2"],
                [1, "-p-1"],
                [0, "-p1"],
                [1, "-p2"],
            ],
    ):
        args = [*x_args, *y_args, *p_args]
        info(f"========== test_cli Begin case -xy: {args}")
        kw=dict(document = doc,
                document_pdf = doc_pdf,
                signature = sig,
                signature_pdf = sig_pdf,
                signature_index = p_idx,
                x_coordinate = x_val,
                y_coordinate = y_val,
                resize_factor = 1,
                pos_args = ["-s", sig_pdf, *args],
                )
        good(**kw)
        diff(**da(kw, x_coordinate = x_val + 0.0001, diff_pages = [p_idx]))
        diff(**da(kw, y_coordinate = y_val + 0.0001, diff_pages = [p_idx]))
        diff(**da(kw, signature_index = 1 - p_idx, diff_pages = [0, 1]))

# -a
def test_cli_anchor():
    rng = Rng(seed=1)
    doc = gen_rnd_pages(seed=rng.random(), n=1, w=500, h=1000)
    sig = Signature(seed=rng.random(), w=200, h=100)
    doc_pdf = gen_pdf(doc, f"Generated doc_pdf with 1 page, {doc[0].w}x{doc[0].h} pt")
    sig_pdf = gen_pdf([sig], f"Generated sig_pdf, {sig.w}x{sig.h} pt")
    for [msg, *args] in [
            ["argument -a/--anchor: invalid choice: 'CW'", "-acW"],
            ["argument -a/--anchor: invalid choice: '7'", "-a7"],
    ]:
        error(document_pdf = doc_pdf, msg=msg, pos_args=["-s", sig_pdf, *args])
    for [[x_1, *args_1], [y_1, *args_2], [x_2, y_2, *args_3]] in rng.cartesian_sample(
            [
                [250],
                [250+50, "-xC+10%"],
                [500-72, "-x", "R-1in"],
                [-72/2.54, "-xL-1cm"],
                [72/2.54, "-x1cm"],
            ], [
                [750],
                [1000, "-yB"],
                [100, "-y10%"],
                [500+330, "-yC+33%"],
            ], [
                [0, 0],
                [100, 50, "-aNW"],
                [0, 50, "-an"],
                [-100, 50, "-aNE"],
                [100, 0, "-aW"],
                [0, 0, "-ac"],
                [-100, 0, "-aE"],
                [100, -50, "-asw"],
                [0, -50, "-aS"],
                [-100, -50, "-ase"],
            ]
    ):
        x = (x_1 + x_2)/doc[0].w
        y = (y_1 + y_2)/doc[0].h
        args = (*args_1, *args_2, *args_3)
        info(f"========== test_cli Begin case -a ({x}, {y}) ~= {args}")
        good(document=doc,
             document_pdf=doc_pdf,
             signature=sig,
             signature_pdf=sig_pdf,
             signature_index=0,
             x_coordinate=x,
             y_coordinate=y,
             resize_factor=1,
             pos_args=["-s", sig_pdf, *args])

# -r, -W, -H
def test_cli_scale():
    rng = Rng(seed=2)
    doc_page_count = 2
    doc = gen_rnd_pages(seed=rng.random(), n=doc_page_count)
    doc_last_page_idx = doc_page_count - 1
    doc_w = doc[doc_last_page_idx].w
    doc_h = doc[doc_last_page_idx].h
    sig = Signature(seed=rng.random())
    doc_pdf = gen_pdf(doc, f"Generated document with {doc_page_count} pages, {doc[0].w}x{doc[0].h} pt")
    sig_pdf = gen_pdf([sig], f"Generated signature, {sig.w}x{sig.h} pt")
    assert sig.w * 1.02 < doc_w * 0.5
    assert sig.h * 1.02 < doc_h * 0.5
    for [msg, *args] in [
            ["Invalid -r option", "-r", "0"],
            ["Invalid -r option", "-r", "-1"],
            ["-r/--resize-factor: invalid float value", "-r", "50%"],
            ["-r/--resize-factor: invalid float value", "-r", "foo"],
    ]:
        error(document_pdf = doc_pdf, msg=msg, pos_args=["-s", sig_pdf, *args])
    for [[r_factor, *r_args], [W_size, *W_args], [H_doc_factor, *H_args]] in rng.cartesian_sample(
            [
                [1],
                [0.3, "-r", "0.3"],
                [100, "-r100"]
            ], [
                [0.5*doc_w],
                [700*72, "-W", "700in"],
                [200, "-W200pt"],
                [1.8*72/2.54, "-W1.8cm"],
            ], [
                [0.5],
                [1.2, "-H120%"],
                [0.25, "-H", "25%"],
                [10, "-H1000%"],
            ]
    ):
        args = [*r_args, *W_args, *H_args]
        info(f"========== test_cli Begin case -rWH: {' '.join(args)}")
        r = min(r_factor,
                W_size/sig.w,
                H_doc_factor*doc_h/sig.h)
        kw=dict(document = doc,
                document_pdf = doc_pdf,
                signature = sig,
                signature_pdf = sig_pdf,
                signature_index = doc_last_page_idx,
                x_coordinate = 0.5,
                y_coordinate = 0.75,
                resize_factor = r,
                pos_args = ["-s", sig_pdf, *args],
                )
        good(**kw)
        diff(**da(kw, resize_factor = r*1.01, diff_pages = [doc_last_page_idx]))

# -f
def test_cli_flatten():
    rng = Rng(seed=3)
    def fill_form(in_pdf, value, desc):
        reader = PdfReader(in_pdf)
        writer = PdfWriter()
        writer.append(reader)
        fields = reader.trailer["/Root"]["/AcroForm"]["/Fields"]
        assert len(fields) == 1
        field_name = fields[0].get_object().get("/T")
        writer.update_page_form_field_values(writer.pages[0], {field_name: value})
        out_pdf = intmp('pdf', f"{in_pdf.name} filled with {field_name}={value}, producing {desc}")
        with open(out_pdf, 'wb') as f:
            writer.write(f)
        return out_pdf
    def has_form(pdf_file): return "/AcroForm" in PdfReader(pdf_file).trailer["/Root"]
    def sign(doc_pdf, sig_pdf, flatten, desc):
        out_pdf = intmp('pdf', f"{doc_pdf.name} signed with {sig_pdf.name}, {'' if flatten else 'NOT '}flattened, producing {desc}")
        runc("pdf-sign", "-bs", sig_pdf, *([] if flatten else ["--no-flatten"]), "-o", out_pdf, doc_pdf)
        return out_pdf
    d = gen_pdf(sign_pages(pages=gen_rnd_pages(seed=rng.random(), n=1, w=400, h=200),
                           # Known, inconsequential bug: The text field seems to
                           # use absolute coordinates and is unaffected by the
                           # translation applied by sign_pages.
                           signature=TextField("foo"),
                           idx=0, cx=0.5, cy=0.25),
                "Generated d with 1 page with a text field")
    d = fill_form(d, "z", "Write z to field")
    s = gen_pdf([Signature(seed=rng.random(), w=2*72, h=2*72)], "2inx2in signature")
    e = gen_pdf([Empty(w=2*72, h=2*72)], "Empty 2inx2in signature")
    d_fe = sign(d, e, False, f"No op on {d}")
    assert_pdf_almost_equal(d, d_fe)
    d_flat = sign(d, e, True, "{d} flattened, to test whether appearance changes")
    # Whether flattening changes the appearance depends on whether we use qpdf
    # or pdftk. We only require consistency.
    flattening_alters_appearance = None
    try:
        assert_pdf_almost_equal(d, d_flat)
        flattening_alters_appearance = False
    except: pass
    try:
        assert_pdf_almost_equal(d, d_flat, [0])
        flattening_alters_appearance = True
    except: pass
    assert flattening_alters_appearance in [True, False]
    seen = {}
    def do_test(doc, flat, txt, signed, desc):
        key = (flat, txt, signed) if flattening_alters_appearance else (txt, signed)
        if key in seen:
            assert_pdf_almost_equal(doc, seen[key])
            return
        else:
            for other in seen.values():
                assert_pdf_almost_equal(doc, other, [0])
            seen[key] = doc
        assert has_form(doc) == (not flat)
        state_dict = {"doc": doc, "flat": flat, "txt": txt, "signed": signed}
        def recurse(**kw): do_test(**da(state_dict, **kw))
        if not signed:
            recurse(doc=sign(doc, s, False, f"{desc},s"), signed = True, desc = f"{desc},s")
            recurse(doc=sign(doc, s, True, f"{desc},fs"), flat = True, signed = True, desc = f"{desc},fs")
        recurse(doc=sign(doc, e, False, f"{desc},e"), desc = f"{desc},e")
        recurse(doc=sign(doc, e, True, f"{desc},fe"), flat = True, desc = f"{desc},fe")
        if not flat:
            recurse(doc=fill_form(doc, "AAA", f"{desc},a"), txt = "AAA", desc = f"{desc},a")
            recurse(doc=fill_form(doc, "BBB", f"{desc},b"), txt = "BBB", desc = f"{desc},b")
    do_test(d, False, "", False, "d")

# -e
def test_cli_existing():
    rng = Rng(seed=4)
    doc_pdf = gen_pdf(gen_rnd_pages(seed=rng.random(), n=1), "Generated document for testing -e")
    sig_pdf = gen_pdf([Signature(seed=rng.random())], "Generated signature for testing -e")
    def r(*args):
        return runc("pdf-sign", "-bs", sig_pdf, *args, doc_pdf)
    out_1 = intmp('pdf', "out_1")
    assert f"Signed document saved as {out_1}\n" == r("-xL", "-o", out_1)
    out_2 = intmp('pdf', "out_2")
    assert f"Signed document saved as {out_2}\n" == r("-xR", "-o", out_2)
    # Test -e backup
    for args in [[], ["-e", "BackUP"]]:
        backup_out = intmp('pdf', "backup_out")
        assert f"Signed document saved as {backup_out}\n" == r(*args, "-xL", "-o", backup_out)
        assert_pdf_exactly_equal(backup_out, out_1)
        backup_out_2 = intmp('pdf', "backup_out_2")
        runc("cp", backup_out, backup_out_2) # Because assert_pdf_* uses caching
        bu_out = r(*args, "-xR", "-o", backup_out_2)
        assert bu_out.endswith(f"Signed document saved as {backup_out_2}\n")
        assert bu_out.startswith(f"Renamed {backup_out_2} to ")
        assert_pdf_exactly_equal(backup_out_2, out_2)
        [_, backup_file] = m("^.*Renamed .*\\.pdf to ([^\\n]*)\\n.*$", bu_out)
        assert_pdf_exactly_equal(Path(backup_file), out_1)
    # Test -e overwrite
    overwrite_out = intmp('pdf', "overwrite_out")
    assert f"Signed document saved as {overwrite_out}\n" == r("-xL", "-e", "overWRITE", "-o", overwrite_out)
    assert_pdf_exactly_equal(overwrite_out, out_1)
    overwrite_out_2 = intmp('pdf', "overwrite_out_2")
    runc("cp", overwrite_out, overwrite_out_2) # Because assert_pdf_* uses caching
    assert f"Signed document saved as {overwrite_out_2}\n" == r("-xR", "-eOverWrite", "-o", overwrite_out_2)
    assert_pdf_exactly_equal(overwrite_out_2, out_2)
    # Test -e fail
    fail_out = intmp('pdf', "fail_out")
    assert f"Signed document saved as {fail_out}\n" == r("-xL", "-e", "fAiL", "-o", fail_out)
    assert f"Output file {fail_out} already exists\n" == run1("pdf-sign", "-bs", sig_pdf, "-xR", "-e", "fail", "-o", fail_out, doc_pdf)
    # Test -e nonsense
    assert "usage: pdf-sign" in run1("pdf-sign", "-xL", "-e", "nonsense", "-o", intmp('pdf', "nonsense_out"))

# -t
def test_cli_text():
    rng = Rng(seed=5)
    doc_page_count = 2
    doc = gen_rnd_pages(seed=rng.random(), n=doc_page_count)
    doc_last_page_idx = doc_page_count - 1
    doc_pdf = gen_pdf(doc, f"Generated document with {doc_page_count} pages, {doc[0].w}x{doc[0].h} pt")
    txt = Text(text="abcde")
    txt_pdf = gen_pdf([txt], "Generated text signature pdf")
    sig = Signature(seed=rng.random())
    sig_pdf = gen_pdf([sig], f"Generated signature, {sig.w}x{sig.h} pt")
    kw = dict(document = doc,
              document_pdf = doc_pdf,
              signature = txt,
              signature_pdf = txt_pdf,
              signature_index = doc_last_page_idx,
              x_coordinate = 0.5,
              y_coordinate = 0.75,
              resize_factor = 1,
              )
    good(**da(kw, pos_args = ["-t", "abcde"]))
    diff(**da(kw, pos_args = ["-t", "fghij"], diff_pages = [doc_last_page_idx]))
    for [msg, *pos_args] in [
            ["--signature and --text cannot be specified together", "-t", "abcde", "-s", sig_pdf],
            ["In batch mode, --signature or --text must be specified"],
    ]:
        error(document_pdf = doc_pdf, msg=msg, pos_args=pos_args)
