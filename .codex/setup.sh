#!/usr/bin/env bash
set -euo pipefail

if ! command -v xelatex >/dev/null 2>&1 || ! command -v latexmk >/dev/null 2>&1; then
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    latexmk \
    texlive-xetex \
    texlive-lang-portuguese \
    texlive-latex-extra \
    texlive-fonts-recommended
fi

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
