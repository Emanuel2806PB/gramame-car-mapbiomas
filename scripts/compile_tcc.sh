#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root/tcc"
latexmk -xelatex -bibtex -interaction=nonstopmode -halt-on-error main.tex
