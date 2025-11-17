{ default_deps
, pkgs
, system }:

let
  # Imports
  packages = import ../nix/packages.nix;
  pypin = import ../nix/python_pinned.nix system;
  # Helpers
  Packages_with_py = py: pytk: packages (default_deps // { python3 = py; python3_with_tk = pytk; });
  Packages_with_pytk = py: Packages_with_py py (py.withPackages (ps: with ps; [ tkinter ]));
  pdftk_deps = default_deps // { qpdf_or_pdftk = pkgs.pdftk; };
  # Packages built with different sets of dependencies
  packages_default = packages default_deps;
  packages_notkinter = Packages_with_py pkgs.python3 pkgs.python3;
  packages_py36 = Packages_with_pytk pypin.python36;
  packages_py37 = Packages_with_pytk pypin.python37;
  packages_py314 = Packages_with_pytk pypin.python314;
  packages_pdftk = packages pdftk_deps;
  inherit (pkgs.lib) optional optionals;
  code_sync = pkgs.stdenv.mkDerivation {
    name = "check-code_sync";
    src = packages_default.pdf-sign.src;
    buildPhase = ''
      mkdir -p $out
      sed -n '/^def text_to_pdf/,/^def / p' $src/pdf-sign | head -n-1 > sync-pdf-sign
      sed -n '/^def text_to_pdf/,/^def / p' $src/pdf-from-text | head -n-1 > sync-pdf-from-text
      cmp sync-pdf-sign sync-pdf-from-text
    '';
  };
  copyright_and_version = let
    v = packages_default.pdf-sign.version;
  in assert v == packages_default.pdf-create-empty.version;
    assert v == packages_default.pdf-from-text.version;
    pkgs.stdenv.mkDerivation {
    name = "check-copyright-and-version";
    src = ./..;
    buildPhase = ''
      mkdir -p $out
      years="2021-2025"
      [ `grep -Ec "^Copyright © $years " LICENSE` == 1 ]
      for file in pdf-sign pdf-create-empty pdf-from-text; do
        [ `grep -Ec "^# Copyright © $years " $file` == 1 ]
        [ `grep -Ec "^ *epilog='(Part of )?pdf-sign v${v} © $years " $file` == 1 ]
      done
    '';
  };
  test = has_gui: test_name: program: check_name: let
    # Dependencies for running tests
    python3_for_testing = pkgs.python3.withPackages (ps: (with ps; [
      numpy
      pypdf
      pytest
      reportlab
    ]));
    test_deps = with pkgs; [
      python3_for_testing
      ghostscript
    ] ++ (optionals has_gui [
      imagemagick
      xdotool
      xvfb-run
    ]);
  in pkgs.stdenv.mkDerivation {
    name = "check-${check_name}";
    src = ./.;
    dontUnpack = true;
    dontPatch = true;
    dontFixup = true;
    dontInstall = true;
    nativeBuildInputs = test_deps ++ [ program ];
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
    PYTHONDONTWRITEBYTECODE = 1;
    PYTEST_ARGS = [
      "--maxfail=1"
      "--color=yes"
      "-p no:cacheprovider"
      "--log-cli-level=INFO"
    ];
    buildPhase = ''
      mkdir -p $out/home
      export INTMP=$(pwd)
      export HOME=$out/home
      ${if has_gui then ''xvfb-run --server-args "-screen 0 1000x1000x24" \'' else ""}
        pytest -q $src/test_${test_name}.py $PYTEST_ARGS ||
      false # To access temporary files on failure, temporarily change to: cp -r $INTMP $out/
    '';
  };
  test_table = [
    # Xvbf  test_X.py    Package to test                   Check name
    [ false "cli"        packages_default.pdf-sign         "cli"                    ]
    [ false "cli"        packages_notkinter.pdf-sign       "cli_notkinter"          ]
    [ false "cli"        packages_py37.pdf-sign            "cli_py37"               ]
    [ false "cli"        packages_py314.pdf-sign           "cli_py317"              ]
    [ false "cli"        packages_pdftk.pdf-sign           "cli_pdftk"              ]
    [ false "too_old_py" packages_py36.pdf-sign            "too_old_py"             ]
    [ true  "gui"        packages_default.pdf-sign         "gui"                    ]
    [ true  "gui"        packages_py37.pdf-sign            "gui_py37"               ]
    [ true  "gui"        packages_py314.pdf-sign           "gui_py317"              ]
    [ true  "gui"        packages_pdftk.pdf-sign           "gui_pdftk"              ]
    [ false "empty"      packages_default.pdf-sign         "empty"                  ]
    [ false "empty"      packages_default.pdf-create-empty "empty_standalone"       ]
    [ false "empty"      packages_py37.pdf-sign            "empty_py37"             ]
    [ false "empty"      packages_py37.pdf-create-empty    "empty_py37_standalone"  ]
    [ false "empty"      packages_py314.pdf-sign           "empty_py317"            ]
    [ false "empty"      packages_py314.pdf-create-empty   "empty_py317_standalone" ]
    [ false "empty"      packages_pdftk.pdf-sign           "empty_pdftk"            ]
    [ false "empty"      packages_pdftk.pdf-create-empty   "empty_pdftk_standalone" ]
    [ false "text"       packages_default.pdf-sign         "text"                   ]
    [ false "text"       packages_default.pdf-from-text    "text_standalone"        ]
    [ false "text"       packages_py37.pdf-sign            "text_py37"              ]
    [ false "text"       packages_py37.pdf-from-text       "text_py37_standalone"   ]
    [ false "text"       packages_py314.pdf-sign           "text_py317"             ]
    [ false "text"       packages_py314.pdf-from-text      "text_py317_standalone"  ]
    [ false "text"       packages_pdftk.pdf-sign           "text_pdftk"             ]
    [ false "text"       packages_pdftk.pdf-from-text      "text_pdftk_standalone"  ]
  ];
in (builtins.listToAttrs (builtins.map
  (x: let x0 = builtins.elemAt x 0;
          x1 = builtins.elemAt x 1;
          x2 = builtins.elemAt x 2;
          x3 = builtins.elemAt x 3;
      in { name = x3; value = test x0 x1 x2 x3; })
  test_table)) // { inherit code_sync copyright_and_version; }
