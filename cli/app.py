"""Compatibilidade para imports legados da CLI."""

from . import build_parser
from . import main
from . import parse_data_iso
from . import run_command

__all__ = ["build_parser", "main", "parse_data_iso", "run_command"]
