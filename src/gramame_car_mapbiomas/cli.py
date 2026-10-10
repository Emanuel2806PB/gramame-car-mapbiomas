from __future__ import annotations

import argparse
import sys

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compara vegetação nativa declarada no CAR com classes naturais do MapBiomas."
    )
    parser.add_argument("--config", required=True, help="Caminho do arquivo YAML de configuração.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = run_pipeline(args.config)
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    print(f"Resultados gravados em: {output}")
    return 0

