{ pkgs
, pdf-sign }:

let
  python3_for_generate_gifs = pkgs.python3.withPackages (ps: with ps; [
    numpy
    pypdf
    reportlab
  ]);
  svenssonaxel-st = pkgs.st.overrideAttrs {
    src = pkgs.fetchgit {
      url = "https://github.com/svenssonaxel/st.git";
      rev = "e17240b";
      hash = "sha256-s/z6zM6FrZ0yXzviCqrjCqj6eEZ+RYGe359WX8VsOLE=";
    };
  };
  package = pkgs.stdenv.mkDerivation {
    name = "readme-gifs";
    src = ./.;
    dontUnpack = true;
    dontPatch = true;
    dontFixup = true;
    dontInstall = true;
    nativeBuildInputs = [
      pdf-sign
      python3_for_generate_gifs
      svenssonaxel-st
    ] ++ (with pkgs; [
      elementary-xfce-icon-theme # for evince
      evince
      exiftool
      ghostscript
      gifsicle
      imagemagick # convert command
      xdotool
      xorg.xrandr
      xvfb-run
    ]);
    BASHRC = pkgs.writeTextFile {
      name = ".bashrc";
      text = ''
        PS0="\e[0m";
        PS1="\n\[\033[0;4;1;35m\]\w\[\033[0;39;42m\]>\[\033[0;1;2m\]";
        HOME=$HOME_bu # Seems like st sets $HOME
        alias ls='ls --color=auto'
        suppress_stderr() { "$@" 2>/dev/null; }
        alias evince='suppress_stderr evince' # Suppress warnings
      '';
    };
    BASHINTERACTIVE = "${pkgs.bashInteractive}/bin/bash";
    FONTCONFIG_FILE = pkgs.makeFontsConf {
      fontDirectories = with pkgs; [
        dejavu_fonts
        freefont_ttf
      ];
      # The `includes` argument defaults to [ "/etc/fonts/conf.d" ] which does
      # not exist in a nix build environment. Without it, fontconfig will
      # silently select the wrong font e.g. a monospace font when sans-serif is
      # requested.
      includes = [ "${pkgs.fontconfig.out}/etc/fonts/conf.d" ];
    };
    PDF_SIGN_UNDOCUMENTED_OVERRIDE_DEFAULT_CUSTOM_TEXT = "2025-10-28"; # For reproducibility
    PYTHONDONTWRITEBYTECODE = 1;
    WIN_HEIGHT = 920;
    WIN_WIDTH = 722;
    buildPhase = ''
      mkdir -p $out
      export HOME=$TMPDIR/home
      export HOME_bu=$HOME
      export XDG_CACHE_HOME="$TMPDIR/.cache"
      export XDG_DATA_HOME="$TMPDIR/.data"
      mkdir -p $HOME/.pdf_signatures
      cp $src/example-initials.pdf $HOME/.pdf_signatures/'initials ᛈ 𐤉 ᚱ.pdf'
      cp $src/example-signature.pdf $HOME/.pdf_signatures/'signature ᛈᛗ𐤄ᛜ 𐤉ᚠ ᚱᚢᚱ𐤃ᚹ.pdf'
      exiftool -Title= -o example-doc.pdf $src/example-doc.pdf
      pdf-sign -b -s $src/example-sig1.pdf \
        -x 20.5% -y 80% -r 1.16 \
        -o $HOME/'ᛉᛉ𐤅𐤇𐤁_ᛖ𐤉ᚱᛜ𐤀.pdf' \
        example-doc.pdf
      cd $HOME
      xvfb-run \
        --server-args "-screen 0 "$WIN_WIDTH"x"$WIN_HEIGHT"x24" \
        python3 $src/generate-example-use-gif.py
      python3 $src/generate-example-signature-gif.py
    '';
  };
  check = pkgs.stdenv.mkDerivation {
    name = "check-readme-gifs";
    src = ./..;
    dontUnpack = true;
    dontPatch = true;
    dontFixup = true;
    dontInstall = true;
    buildPhase = ''
      mkdir $out
      cmp $src/example-use.gif ${package}/example-use.gif
      cmp $src/example-signature.gif ${package}/example-signature.gif
    '';
  };
in { inherit package check; }
