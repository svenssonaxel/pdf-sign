# pdf-sign

## What

A tool to sign PDF files, with Linux support.
We are here referring to the visible, non-cryptographic squiggles.

![](README-example.gif)

## How

First, create one or several signatures in the form of small PDF files with transparent backgrounds.
The recommended way is:
* Use the included `pdf-create-empty` tool to create an empty, transparent PDF file.
  If 3×2 inch suits you, you can use [empty-3inx2in.pdf](empty-3inx2in.pdf) directly.
* Use an application of your choice to sign it.
  You can for example use Okular's Freehand Line, or transfer it to your smartphone and use Adobe Acrobat Reader.
  Keep in mind that it's the center of this mini-page that will be used for positioning the signature.
* Put the signed file in your signature directory.
  The signature directory is `$PDF_SIGNATURE_DIR`, `$XDG_CONFIG_HOME/pdf_signatures`, `$HOME/.config/pdf_signatures` or `$HOME/.pdf_signatures/`; the first one that exists. Use `pdf-sign -h` to confirm which one will be used on your system.

You can now use the `pdf-sign` tool interactively (or non-interactively) to sign PDF files.
The GUI is self documented and allows both keyboard-only and pointer-only operation.

Run `pdf-sign -h` or `pdf-create-empty -h` for details.

**Installation**

* Install dependencies
  * `python3.7` or later
  * Python module `tkinter` (only needed for interactive use)
  * `gs` (Ghostscript)
  * `qpdf` or `pdftk` (at least one of them)
  * `pdfinfo`
* Copy one or both tools to a directory in your `$PATH`.

**Installation on Debian**

```sh
apt-get update
apt-get install -y coreutils git python3 python3-tk ghostscript pdftk poppler-utils
git clone https://github.com/svenssonaxel/pdf-sign.git
cd pdf-sign
cp pdf-sign pdf-create-empty /usr/local/bin/
```

## Why

There appears to be a lack of applications that run on Linux and allow for attaching free-hand signatures to PDF files in a good way.

(Non-)alternatives include:

* **Xournal and Xournal++:**
  Allows free-hand annotations, but not saving those for later use.
  Allows inserting images and .pdf files but will rasterize them rather than retain the vector graphics, resulting in lower quality.
* **LibreOffice Draw:**
  Allows inserting images and .pdf files but will rasterize them rather than retain the vector graphics, resulting in lower quality.
* **Okular:**
  Allows free-hand annotations, but not saving those for later use.
  Allows inserting custom saved stamps, but will rasterize them rather than retain the vector graphics, resulting in lower quality.
  (Older versions of Okular might save the stamps in a way that isn't visible in other PDF readers.)
* **Evince:**
  Allows certain kinds of annotations, but nothing that can look like a free-hand signature.
* **pdftk**, **ghostscript**, and other command-line tools:
  Allows superimposing .pdf files, but not interactively selecting where.
