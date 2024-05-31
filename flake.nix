{
  description = "Tool to visually sign PDF files";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  inputs.utils.url = "github:numtide/flake-utils";
  outputs = { self,
              nixpkgs,
              utils
            }: utils.lib.eachDefaultSystem(system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
      default_deps = {
        inherit (pkgs)
          ghostscript
          lib
          makeBinaryWrapper
          poppler_utils
          python3
          stdenv
          which
        ;
        python3_with_tk = pkgs.python3.withPackages (ps: with ps; [ tkinter ]);
        qpdf_or_pdftk = pkgs.qpdf;
      };
    in {
      packages = (import ./nix/packages.nix) default_deps;
      checks = (import ./tests/checks.nix) {
        inherit
          default_deps
          pkgs
          system
        ;
      };
    });
}
