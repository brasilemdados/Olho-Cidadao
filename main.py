"""Ponto de entrada enxuto da CLI do projeto."""

from cli import build_parser
from cli import main
from cli import parse_data_iso
from cli import run_command

__all__ = ["build_parser", "main", "parse_data_iso", "run_command"]


if __name__ == "__main__":
    main()
