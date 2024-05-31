from pypdf import PdfReader
from intmp import intmp
from util import runc
import numpy as np
from functools import cache

@cache
def pdf_page_sizes(path):
    r = PdfReader(path)
    assert not r.is_encrypted
    ret = []
    for p in r.pages:
        box = getattr(p, "cropbox", None) or p.mediabox
        ret.append((float(box.width), float(box.height)))
    return ret

def _assert_pdf_equal_helper(first_pdf, other_pdf, ppm_fn):
    first_pages = pdf_page_sizes(first_pdf)
    first_ppms = [pdf_to_ppm(first_pdf, pageidx)
                  for pageidx in range(len(first_pages))]
    other_pages = pdf_page_sizes(other_pdf)
    assert len(first_pages)==len(other_pages), f"{first_pdf} has {len(first_pages)} pages but {other_pdf} has {len(other_pages)} pages."
    for pageidx, other_pagesize in enumerate(other_pages):
        assert first_pages[pageidx]==other_pagesize, f"Page {pageidx} size differs: {first_pdf} has {first_pages[pageidx]} but {other_pdf} has {other_pagesize}"
        other_ppm = pdf_to_ppm(other_pdf, pageidx)
        ppm_fn(first_ppms[pageidx], other_ppm, pageidx)

def assert_pdf_almost_equal(first_pdf, other_pdf, except_page_idxs=[]):
    def ppm_fn(a, b, pageidx):
        if pageidx in except_page_idxs:
            assert_ppm_not_almost_equal(a, b)
        else:
            assert_ppm_almost_equal(a, b)
    _assert_pdf_equal_helper(first_pdf, other_pdf, ppm_fn)

def assert_pdf_exactly_equal(first_pdf, other_pdf, except_page_idxs=[]):
    def ppm_fn(a, b, pageidx):
        if pageidx in except_page_idxs:
            assert_ppm_not_almost_equal(a, b)
        else:
            assert_ppm_exactly_equal(a, b)
    _assert_pdf_equal_helper(first_pdf, other_pdf, ppm_fn)

@cache
def pdf_to_ppm(path, pageidx):
    out_ppm = intmp('ppm', f"{path.name} page {pageidx+1} rasterized")
    runc("gs", "-dSAFER", "-dBATCH", "-dNOPAUSE",
         "-sDEVICE=ppmraw", "-r144",
         f"-dFirstPage={pageidx+1}", f"-dLastPage={pageidx+1}",
         f"-sOutputFile={out_ppm}",
         path)
    return out_ppm

def _ppm_read_tokens(fp, n):
    toks = []
    token = bytearray()
    while len(toks) < n:
        b = fp.read(1)
        if not b:
            raise ValueError("Unexpected EOF in PNM header")
        if b == b'#':
            while b not in (b'\n', b''):
                b = fp.read(1)
            continue
        if b.isspace():
            if token:
                toks.append(token.decode('ascii'))
                token.clear()
        else:
            token.extend(b)
    return toks

def read_ppm(path):
    with open(path, 'rb') as fp:
        magic, w_str, h_str, maxval_str = _ppm_read_tokens(fp, 4)
        w, h, maxval = int(w_str), int(h_str), int(maxval_str)
        assert magic == "P6"
        assert maxval==255
        nbytes = w * h * 3
        buf = fp.read(nbytes)
        assert len(buf) == nbytes
        img = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 3)
        return (img, w, h)

def _ppm_equality_helper(a_path, b_path):
    a, wa, ha = read_ppm(a_path)
    b, wb, hb = read_ppm(b_path)
    assert (wa, ha) == (wb, hb), f"{a_path.name} has size {wa}x{ha} but {b_path.name} has size {wb}x{hb}"
    adiff = np.abs(a.astype(np.int32) - b.astype(np.int32)).sum(axis=2)
    vals, counts = np.unique(adiff, return_counts=True)
    hist = { int(v): int(c) for v, c in zip(vals, counts) }
    big_errors = sum(c for v, c in zip(vals, counts) if v > 3)
    return big_errors, hist, wa*ha

def assert_ppm_almost_equal(a_path, b_path):
    big_errors, hist, pixels = _ppm_equality_helper(a_path, b_path)
    assert big_errors <= pixels*0.00001, f"{a_path.name} and {b_path.name} differ with {big_errors} big errors (should be <= {pixels*0.00001}). Histogram: {hist}"

def assert_ppm_not_almost_equal(a_path, b_path):
    big_errors, hist, pixels = _ppm_equality_helper(a_path, b_path)
    assert big_errors > pixels*0.0001, f"{a_path.name} and {b_path.name} differ with {big_errors} big errors (should be > {pixels*0.0001}). Histogram: {hist}"

def assert_ppm_exactly_equal(a_path, b_path):
    _, hist, pixels = _ppm_equality_helper(a_path, b_path)
    assert hist == { 0: pixels }, f"{a_path.name} and {b_path.name} differ (should be equal). Histogram: {hist}"
    assert len(hist) == 1
