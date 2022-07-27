# pdf-sign

## What

A tool to sign PDF files.
We are here referring to the visible, non-cryptographic squiggles.

## How

First, create one or several signatures in the form of small PDF files with transparent backgrounds.
The recommended way is:
* Use the included `pdf-create-empty` tool to create an empty, transparent PDF file.
* Use an application of your choice to sign it.
  You can for example use Okular's Freehand Line, or transfer it to your smartphone and use Adobe Acrobat Reader.
* Put the signed file in `~/.pdf_signatures/`.

You can now use the `pdf-sign` tool interactively (or non-interactively) to sign PDF files.

Run `pdf-sign -h` or `pdf-create-empty -h` for details.

Installation:
* Install dependencies: `python3.7` or later with module `tkinter`, `gs` (Ghostscript), `pdftk` and `pdfinfo`.
* Copy one or both tools to a directory in your `$PATH`.

Installation on Debian:
```sh
apt-get update && apt-get install -y coreutils ghostscript git pdftk poppler-utils python3 python3-tk
git clone https://github.com/svenssonaxel/pdf-sign.git
cd pdf-sign
cp pdf-sign pdf-create-empty /usr/local/bin/
```

## Why

There appears to be a lack of applications that run on Linux and allow for attaching free-hand signatures to PDF files in a good way.

(Non-)alternatives include:

* Okular: Allows for drawing 'Freehand Line' annotations, but not saving those for later use.
  Allows for inserting custom saved stamps, but these will not be visible in other PDF readers.
* Evince: Allows for certain kinds of annotations, but nothing that can serve as a signature.
* pdftk, ghostscript, and other command-line tools: Allows for inserting stamps, but not interactively selecting where.
