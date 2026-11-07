#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root/apresentacao"
latexmk -xelatex -interaction=nonstopmode -halt-on-error apresentacao.tex
