# GUI tests.
# - Generate PDF documents/signatures.
# - Sign them in various ways using CLI pdf-sign.
# - Sign them in various equivalent ways using GUI pdf-sign.
# - Compare the resulting PDFs using exact visual equality.
# These tests are meant to test only the GUI interface. They test the
# correctness of the output only via reliance on the CLI tests.

import subprocess, time
import numpy as np
from functools import cache
from logging import info

from util import runc, runbg, run_env, DynVar
from intmp import intmp
from gen_pdf import Signature, gen_rnd_pages, sign_pages, gen_pdf, Rng
from compare_pdf import assert_pdf_exactly_equal, read_ppm

def screenshot(msg="Screenshot"):
    outfile = intmp('ppm', msg)
    runc("magick", "import", "-window", "root",
         "-depth", 8, # bits per channel
         outfile)
    return outfile

def xdo(*args): runc("xdotool", *args)
def press(*keys):
    for key in keys:
        info(f"Press {key}")
        light = key.startswith("Alt+") or key.startswith("+")
        xdo("key", key.strip("+"))
        time.sleep(0.2 if light else 1)
def click(x, y): xdo("mousemove", str(x), str(y), "click", "1")

def display_is_black(msg):
    img, *_ = read_ppm(screenshot(msg))
    vals = np.unique(img)
    return len(vals) == 1 and vals[0]==0

WIN_WIDTH = 1000
WIN_HEIGHT = 1000

OUTFILE = object() #sentinel value

def pdf_sign_gui(args, keys, expect_abort = False):
    return _pdf_sign_gui(args, keys, expect_abort, frozenset(run_env().items()))
@cache
def _pdf_sign_gui(args, keys, expect_abort, _):
    assert display_is_black("Assert black display before GUI start")
    assert OUTFILE in args
    outfile = intmp('pdf', "GUI signed PDF")
    args = [outfile if x == OUTFILE else x for x in args]
    proc = runbg("pdf-sign", *args)
    time.sleep(1)
    try: xdo("search",
             "--sync",
             "--onlyvisible",
             "--class", "pdf-sign",
             "windowmove", "0", "0",
             "windowsize", WIN_WIDTH, WIN_HEIGHT,
             "windowfocus")
    except subprocess.TimeoutExpired:
        info("xdotool could not find pdf-sign window")
        proc.kill()
        proc.wait()
        raise
    time.sleep(1) # Allow for loading/rendering
    assert not display_is_black("Assert not black display after GUI start")
    press(*keys)
    try:
        proc.wait(timeout=40)
    except subprocess.TimeoutExpired:
        info(f"Process did not exit in time, attempting to kill: pdf-sign {' '.join(map(str, args))}")
        proc.kill()
        proc.wait()
        raise
    out, err = proc.communicate()
    assert proc.returncode == 0, f"pdf-sign GUI exited with code {proc.returncode}.\nSTDOUT:\n{out}\nSTDERR:\n{err}"
    assert err == "", f"pdf-sign GUI produced output on stderr:\n{err}"
    if expect_abort:
        assert "Aborted" in out, f"pdf-sign GUI did not report abort on stdout:\n{out}"
    else:
        assert str(outfile) in out, f"pdf-sign GUI did not report output file {outfile} on stdout:\n{out}"
    assert display_is_black("Assert black display after GUI shutdown")
    return outfile

@cache
def pdf_sign_cli(*args):
    assert OUTFILE in args
    outfile = intmp('pdf', "CLI signed PDF")
    args = [outfile if x == OUTFILE else x for x in args]
    out = runc("pdf-sign", *args)
    assert str(outfile) in out, f"pdf-sign GUI did not report output file {outfile} on stdout:\n{out}"
    return outfile

def test_gui():
    rng = Rng(seed=0)
    page_count = 3
    doc = gen_rnd_pages(seed=rng.random(), n=page_count)
    sig = Signature(seed=rng.random())
    doc_pdf = gen_pdf(doc, f"Generated document with {page_count} pages")
    sig_pdf = gen_pdf([sig], "Generated signature")

    # helpers
    first_cli_args = DynVar(["-s", sig_pdf])
    first_gui_args = DynVar(["-s", sig_pdf])
    def eq(cli_args, gui_args, *key_seqs):
        for keys in key_seqs:
            info(f"========== test_gui Begin case eq({cli_args}, {gui_args}, {keys})")
            assert_pdf_exactly_equal(
                pdf_sign_cli("-bo", OUTFILE, *first_cli_args(), *cli_args, doc_pdf),
                pdf_sign_gui(("-o", OUTFILE, *first_gui_args(), *gui_args, doc_pdf), (*keys,)))
    def neq(except_pages, cli_args, gui_args, *key_seqs):
        assert len(except_pages) > 0, "neq must have at least one except_page_idx"
        except_page_idxs = [page - 1 for page in except_pages]
        for keys in key_seqs:
            info(f"========== test_gui Begin case neq(idxs{except_page_idxs}, {cli_args}, {gui_args}, {keys})")
            assert_pdf_exactly_equal(
                pdf_sign_cli("-bo", OUTFILE, *first_cli_args(), *cli_args, doc_pdf),
                pdf_sign_gui(("-o", OUTFILE, *first_gui_args(), *gui_args, doc_pdf), (*keys,)),
                except_page_idxs=except_page_idxs)
    def aborted(*keys):
        info(f"========== test_gui Begin case aborted{keys}")
        outfile = pdf_sign_gui(("-o", OUTFILE, *first_gui_args(), doc_pdf), keys, expect_abort = True)
        assert not outfile.exists()

    # File -> Sign & Exit
    eq([], [],
       ["space"],
       ["s"],
       ["S"],
       ["Alt+f", "s"],
       ["Alt+f", "S"],
       ["Alt+f", "Return"],
       ["Alt+f", "KP_Enter"])
    eq(["-p1"], ["-p1"], ["s"])
    eq(["-p2"], ["-p2"], ["s"])
    eq(["-p3"], ["-p3"], ["s"])
    eq([], ["-p3"], ["s"])
    eq(["-p3"], [], ["s"])
    neq([1, 2], ["-p1"], ["-p2"], ["s"])
    neq([1, 2], ["-p2"], ["-p1"], ["s"])
    neq([1, 3], ["-p1"], ["-p3"], ["s"])
    neq([1, 3], ["-p1"], [], ["s"])
    neq([1, 3], ["-p3"], ["-p1"], ["s"])
    neq([1, 3], [], ["-p1"], ["s"])
    neq([2, 3], ["-p2"], ["-p3"], ["s"])
    neq([2, 3], ["-p2"], [], ["s"])
    neq([2, 3], ["-p3"], ["-p2"], ["s"])
    neq([2, 3], [], ["-p2"], ["s"])

    # File -> Abort & Exit
    aborted("Escape")
    aborted("q")
    aborted("Q")
    aborted("Alt+f", "a")
    aborted("Alt+f", "A")
    aborted("Alt+f", "+Down", "Return")

    # Page -> First page
    eq(["-p1"], [],
       ["Home", "s"],
       ["KP_Home", "s"],
       ["Alt+p", "f", "s"],
       ["Alt+P", "F", "s"],
       ["Alt+p", "Return", "s"])
    neq([1, 2], ["-p2"], ["-p2"], ["Home", "s"])
    neq([1, 3], [], [], ["Home", "s"])

    # Page -> Previous page
    eq(["-p1"], ["-p1"], ["Prior", "s"]) # No wraparound
    eq(["-p2"], [],
       ["Prior", "s"],
       ["KP_Prior", "s"],
       ["Page_Up", "s"],
       ["KP_Page_Up", "s"],
       ["Alt+p", "p", "s"],
       ["Alt+p", "+Down", "Return", "s"],
       ["Alt+p", "+KP_Up", "+Up", "+Up", "Return", "s"],
       )
    eq(["-p1"], [],
       ["Prior", "Prior", "s"],
       ["Prior", "Prior", "Prior", "s"], # No wraparaound
       )
    neq([2, 3], [], [], ["Prior", "s"])

    # Page -> Next page
    eq([], [], ["Next", "s"]) # No wraparound
    eq(["-p2"], ["-p1"],
       ["Next", "s"],
       ["KP_Next", "s"],
       ["Page_Down", "s"],
       ["KP_Page_Down", "s"],
       ["Alt+p", "n", "s"],
       ["Alt+p", "+Down", "+KP_Down", "Return", "s"],
       ["Alt+p", "+Up", "+Up", "Return", "s"])
    eq([], ["-p1"],
       ["Next", "Next", "s"],
       ["Next", "Next", "Next", "s"], # No wraparound
       )
    neq([1, 2], ["-p1"], ["-p1"], ["Next", "s"])

    # Page -> Last page
    eq([], ["-p1"],
       ["End", "s"],
       ["KP_End", "s"],
       ["Alt+p", "l", "s"],
       ["Alt+p", "+Down", "+Down", "+Down", "Return", "s"],
       ["Alt+p", "+Up", "Return", "s"])
    neq([1, 3], ["-p1"], ["-p1"], ["End", "s"])
    neq([2, 3], ["-p2"], ["-p2"], ["End", "s"])

    sig2 = Signature(seed=rng.random())
    sig3 = Signature(seed=rng.random())
    sig2_pdf = gen_pdf([sig2], "2nd generated signature")
    sig3_pdf = gen_pdf([sig3], "3nd generated signature")
    sig_dir = intmp('dir', "Signature directory used in GUI mode")
    runc("mkdir", sig_dir)
    runc("cp", sig_pdf, sig_dir / "sig1.pdf")
    runc("cp", sig2_pdf, sig_dir / "sig2.pdf")
    runc("cp", sig3_pdf, sig_dir / "sig3.pdf")
    with run_env({"PDF_SIGNATURE_DIR": str(sig_dir)}), first_cli_args([]), first_gui_args([]):

        # Signature -> Previous signature
        neq([3], ["-s", sig_pdf], ["2", "s"])
        # Wrap-around with 3 signature plus text option
        eq(["-s", sig_pdf], [],
           ["s"],
           ["1", "s"],
           ["2", "Alt+i", "p", "s"],
           ["3", "Ctrl+Left", "Ctrl+KP_Left", "s"])
        eq(["-s", sig2_pdf], [],
           ["Ctrl+Left", "Ctrl+Left", "Ctrl+KP_Left", "s"],
           ["2", "s"],
           ["3", "Ctrl+Left", "s"])
        eq(["-s", sig3_pdf], [],
           ["Ctrl+Left", "Alt+I", "P", "s"])

        # Signature -> Next signature
        eq(["-s", sig_pdf], [],
           ["2", "Alt+i", "n", "Ctrl+Right", "Ctrl+Right", "s"],
           ["3", "Ctrl+KP_Right", "Ctrl+Right", "s"])
        eq(["-s", sig2_pdf], [],
           ["Ctrl+Right", "s"],
           ["3", "Ctrl+Right", "Ctrl+Right", "Ctrl+KP_Right", "s"])
        eq(["-s", sig3_pdf], [],
           ["Ctrl+Right", "Alt+I", "N", "s"])

        # Signature -> Signature 1, 2, 3
        eq(["-s", sig_pdf], [],
           ["s"],
           ["1", "s"],
           ["Alt+i", "1", "s"])
        neq([3], ["-s", sig_pdf], [],
            ["2", "s"],
            ["Alt+i", "2", "s"],
            ["3", "s"],
            ["Alt+i", "3", "s"])
        eq(["-s", sig2_pdf], [],
           ["2", "s"],
           ["Alt+i", "2", "s"])
        neq([3], ["-s", sig2_pdf], [],
            ["s"],
            ["1", "s"],
            ["Alt+i", "1", "s"],
            ["3", "s"],
            ["Alt+i", "3", "s"])
        eq(["-s", sig3_pdf], [],
           ["3", "s"],
           ["Alt+i", "3", "s"])
        neq([3], ["-s", sig3_pdf], [],
            ["s"],
            ["1", "s"],
            ["Alt+i", "1", "s"],
            ["2", "s"],
            ["Alt+i", "2", "s"])

        # Signature -> Custom text
        eq(["-t", "abcde"], ["-t", "abcde"], ["s"])
        neq([3], ["-t", "abcde"], ["-t", "fghij"], ["s"])
        eq(["-t", "abcde"], ["-t", "fghij", "-t", "abcde"], ["Ctrl+Right", "s"])
        eq(["-s", sig_pdf], ["-t", "fghij", "-t", "abcde"], ["Ctrl+Right", "Ctrl+Right", "s"])
        eq(["-s", sig2_pdf], ["-t", "fghij", "-t", "abcde"], ["Ctrl+Right", "Ctrl+Right", "Ctrl+Right", "s"])
        eq(["-s", sig2_pdf], ["-t", "abcde"], ["Ctrl+Right", "Ctrl+Right", "s"])
        eq(["-t", "abcde"], [],
           ["Alt+i", "t", "+a", "+b", "+c", "+d", "+e", "Return", "s"],
           ["t", "+a", "+b", "+c", "+d", "+e", "Return", "s"],
           ["T", "+a", "+b", "+c", "+d", "+e", "KP_Enter", "s"])

    # Signature -> Enlarge signature
    eq(["-r1.1"], [],
       ["plus", "s"],
       ["KP_Add", "s"],
       ["Alt+i", "e", "s"],
       ["Alt+i", "E", "s"],
       ["Alt+i", "Return", "s"])
    eq(["-r1.21"], [],
       ["plus", "KP_Add", "s"])

    # Signature -> Shrink signature
    eq(["-r", 1/1.1], [],
       ["minus", "s"],
       ["KP_Subtract", "s"],
       ["Alt+i", "s", "s"],
       ["Alt+i", "S", "s"],
       ["Alt+i", "+Down", "Return", "s"])
    eq(["-r", 1/1.21], [],
       ["minus", "KP_Subtract", "s"])

    # Signature -> Move signature left 2%
    eq(["-x48%"], [],
       ["Left", "s"],
       ["KP_Left", "s"],
       ["Alt+i", "l", "s"],
       ["Alt+I", "L", "s"],
       ["Alt+i", "+Down", "+Down", "Return", "s"])
    eq(["-x46%"], [],
       ["Left", "Left", "s"])

    # Signature -> Move signature down 2%
    eq(["-y77%"], [],
       ["Down", "s"],
       ["KP_Down", "s"],
       ["Alt+i", "d", "s"],
       ["Alt+I", "D", "s"],
       ["Alt+i", "+Down", "+Down", "+Down", "Return", "s"])
    eq(["-y79%"], [],
       ["Down", "Down", "s"])

    # Signature -> Move signature up 2%
    eq(["-y73%"], [],
       ["Up", "s"],
       ["KP_Up", "s"],
       ["Alt+i", "u", "s"],
       ["Alt+I", "U", "s"],
       ["Alt+i", "+Down", "+Down", "+Down", "+Down", "Return", "s"])
    eq(["-y71%"], [],
       ["Up", "Up", "s"])

    # Signature -> Move signature right 2%
    eq(["-x52%"], [],
       ["Right", "s"],
       ["KP_Right", "s"],
       ["Alt+i", "r", "s"],
       ["Alt+I", "R", "s"],
       ["Alt+i", "+Down", "+Down", "+Down", "+Down", "+Down", "Return", "s"],
       ["Alt+i", "+Up", "+Up", "+Up", "+Up", "+Up", "Return", "s"])
    eq(["-x54%"], [],
       ["Right", "Right", "s"])

    # Signature -> Move signature left 1pt
    def xpt(pt):
        return f"-x{100.0 * pt / doc[0].w}%"
    neq([3], [xpt(400)], [xpt(401)], ["s"])
    neq([3], [xpt(400)], [xpt(402)], ["s"])
    neq([3], [xpt(401)], [xpt(402)], ["s"])
    eq([xpt(400)], [xpt(400)], ["s"])
    eq([xpt(400)], [xpt(401)],
       ["Shift+Left", "s"],
       ["Shift+KP_Left", "s"],
       ["Alt+i", "f", "s"],
       ["Alt+I", "F", "s"],
       ["Alt+i", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "Return", "s"],
       ["Alt+i", "+Up", "+Up", "+Up", "+Up", "Return", "s"])
    eq([xpt(400)], [xpt(402)],
       ["Shift+Left", "Shift+Left", "s"])

    # Signature -> Move signature down 1pt
    def ypt(pt):
        return f"-y{100.0 * pt / doc[0].h}%"
    neq([3], [ypt(400)], [ypt(399)], ["s"])
    neq([3], [ypt(400)], [ypt(398)], ["s"])
    neq([3], [ypt(399)], [ypt(398)], ["s"])
    eq([ypt(400)], [ypt(400)], ["s"])
    eq([ypt(400)], [ypt(399)],
       ["Shift+Down", "s"],
       ["Shift+KP_Down", "s"],
       ["Alt+i", "o", "s"],
       ["Alt+I", "O", "s"],
       ["Alt+i", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "Return", "s"],
       ["Alt+i", "+Up", "+Up", "+Up", "Return", "s"])
    eq([ypt(400)], [ypt(398)],
       ["Shift+Down", "Shift+Down", "s"])

    # Signature -> Move signature up 1pt
    neq([3], [ypt(400)], [ypt(401)], ["s"])
    neq([3], [ypt(400)], [ypt(402)], ["s"])
    neq([3], [ypt(401)], [ypt(402)], ["s"])
    eq([ypt(400)], [ypt(401)],
       ["Shift+Up", "s"],
       ["Shift+KP_Up", "s"],
       ["Alt+i", "a", "s"],
       ["Alt+I", "A", "s"],
       ["Alt+i", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "Return", "s"],
       ["Alt+i", "+Up", "+Up", "Return", "s"])
    eq([ypt(400)], [ypt(402)],
       ["Shift+Up", "Shift+Up", "s"])

    # Signature -> Move signature right 1pt
    neq([3], [xpt(400)], [xpt(399)], ["s"])
    neq([3], [xpt(400)], [xpt(398)], ["s"])
    neq([3], [xpt(399)], [xpt(398)], ["s"])
    eq([xpt(400)], [xpt(399)],
       ["Shift+Right", "s"],
       ["Shift+KP_Right", "s"],
       ["Alt+i", "i", "s"],
       ["Alt+I", "I", "s"],
       ["Alt+i", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "+Down", "Return", "s"],
       ["Alt+i", "+Up", "Return", "s"])
    eq([xpt(400)], [xpt(398)],
       ["Shift+Right", "Shift+Right", "s"])
