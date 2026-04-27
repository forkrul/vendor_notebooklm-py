# Declarative Python environment for the notebooklm service.
#
# Built inside the Docker image via `nix-build`. Adding a dependency means
# adding a line here — no requirements.txt drift.
#
# `<nixpkgs>` resolves to the channel pinned by the base image
# (nixos/nix), which is updated via `nix-channel --update` in the Dockerfile.
{ pkgs ? import <nixpkgs> {} }:

pkgs.python312.withPackages (ps: with ps; [
  fastapi
  uvicorn
  httpx
  click
  rich
  pydantic
])
