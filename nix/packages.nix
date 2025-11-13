{ lib
, stdenv
, makeBinaryWrapper

, ghostscript
, poppler_utils
, python3
, python3_with_tk
, qpdf_or_pdftk
, which
}:
# Inspired by
# https://github.com/NixOS/nixpkgs/blob/755b915a158c9d588f08e9b08da9f7f3422070cc/pkgs/by-name/pd/pdf-sign/package.nix
# Thanks to github user TomaSajt

let
  path_all_deps = lib.makeBinPath [
    ghostscript
    poppler_utils
    qpdf_or_pdftk
    which
  ];
  path_gs = lib.makeBinPath [ ghostscript ];
  app = { pname, description, script }:
    stdenv.mkDerivation {
      inherit pname;
      version = "0-unstable-2025-10-19";
      src = lib.cleanSourceWith {
        src = ./..;
        filter = (path: type:
          (lib.any (q: (toString q) == path)
            [ ../pdf-sign ../pdf-create-empty ../pdf-from-text ../empty-3inx2in.pdf ]));
      };
      nativeBuildInputs = [ makeBinaryWrapper ];
      buildInputs = [ (if pname == "pdf-sign" then python3_with_tk else python3) ];
      installPhase = ''
        runHook preInstall
        ${script}
        runHook postInstall
      '';
      meta = {
        inherit description;
        homepage = "https://github.com/svenssonaxel/pdf-sign";
        license = lib.licenses.mit;
        mainProgram = pname;
        maintainers = [ {
          email = "mail@axelsvensson.com";
          github = "svenssonaxel";
          githubId = 163858;
          name = "Axel Svensson";
        } ];
        platforms = lib.platforms.unix;
      };
    };
in rec {
  default = pdf-sign;
  pdf-sign = app {
    pname = "pdf-sign";
    description = "Tool to visually sign PDF files";
    script = ''
      install -Dm755 pdf-sign -t $out/libexec
      install -Dm755 pdf-create-empty -t $out/bin
      install -Dm755 pdf-from-text -t $out/libexec
      install -Dm644 empty-3inx2in.pdf -t $out/share/pdf-sign
      makeWrapper $out/libexec/pdf-sign $out/bin/pdf-sign --prefix PATH : ${path_all_deps}
      makeWrapper $out/libexec/pdf-from-text $out/bin/pdf-from-text --prefix PATH : ${path_gs}
    '';
  };
  pdf-create-empty = app {
    pname = "pdf-create-empty";
    description = "Tool to create empty PDF files";
    script = ''
      install -Dm755 pdf-create-empty -t $out/bin
    '';
  };
  pdf-from-text = app {
    pname = "pdf-from-text";
    description = "Tool to create PDF files from text";
    script = ''
      install -Dm755 pdf-from-text -t $out/libexec
      makeWrapper $out/libexec/pdf-from-text $out/bin/pdf-from-text --prefix PATH : ${path_gs}
    '';
  };
}
