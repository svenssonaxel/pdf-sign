system:
let
  oldNixpkgs = rev: hash:
    import (builtins.fetchTree {
      type = "git";
      url = "https://github.com/NixOS/nixpkgs";
      rev = rev;
      narHash = "sha256-${hash}";
    }) { inherit system; };
  nixpkgs2105 = oldNixpkgs
    "fefb0df7d2ab2e1cabde7312238026dcdc972441"
    "ZjBd81a6J3TwtlBr3rHsZspYUwT9OdhDk+a/SgSEf7I=";
  nixpkgs2211 = oldNixpkgs
    "bd15cafc53d0aecd90398dd3ffc83a908bceb734"
    "/HEZNyGbnQecrgJnfE8d0WC5c1xuPSD2LUpB6YXlg4c=";
  nixpkgs2311 = oldNixpkgs
    "7c6e3666e2040fb64d43b209b84f65898ea3095d"
    "MxCVrXY6v4QmfTwIysjjaX0XUhqBbxTWWB4HXtDYsdk=";
  nixpkgs2411 = oldNixpkgs
    "aae12a743f75097dd3a60a8265978b995298babc"
    "CqCX4JG7UiHvkrBTpYC3wcEurvbtTADLbo3Ns2CEoL8=";
  nixpkgs2505 = oldNixpkgs
    "afb2b21ba489196da32cd9f0072e0dce6588a20a"
    "rWtXrcIzU5wm/C8F9LWvUfBGu5U5E7cFzPYT1pHIJaQ=";
in {
  inherit (nixpkgs2105) python36;
  inherit (nixpkgs2211) python37;
  inherit (nixpkgs2311) python38;
  inherit (nixpkgs2411) python39;
  inherit (nixpkgs2505)
    python310
    python311
    python312
    python313
    python314
  ;
}
