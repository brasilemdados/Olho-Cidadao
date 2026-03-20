"""Fachada e orquestracao da CLI do projeto."""

from __future__ import annotations

import argparse
import sys

from configuracao.logger import logger
from infra.errors import UserInputError

from .camara import COMMANDS as CAMARA_COMMANDS
from .comun import CliCommand
from .comun import CommandHandler
from .comun import parse_data_iso
from .fontes import COMMANDS as FONTES_COMMANDS
from .interface import COMMANDS as INTERFACE_COMMANDS
from .pipelines import COMMANDS as PIPELINE_COMMANDS
from .portal import COMMANDS as PORTAL_COMMANDS

COMMANDS: tuple[CliCommand, ...] = (
    *INTERFACE_COMMANDS,
    *CAMARA_COMMANDS,
    *PORTAL_COMMANDS,
    *PIPELINE_COMMANDS,
    *FONTES_COMMANDS,
)

HANDLERS: dict[str, CommandHandler] = {
    nome: comando.handler
    for comando in COMMANDS
    for nome in (comando.name, *comando.aliases)
}


def build_parser() -> argparse.ArgumentParser:
    """Constroi o parser principal da CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "CLI de dados legislativos, orçamentários e de enriquecimento "
            "investigativo com APIs governamentais."
        )
    )
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")
    subparsers.required = True

    for comando in COMMANDS:
        kwargs = {"help": comando.help}
        if comando.aliases:
            kwargs["aliases"] = list(comando.aliases)
        parser_comando = subparsers.add_parser(comando.name, **kwargs)
        if comando.configure_parser is not None:
            comando.configure_parser(parser_comando)

    return parser


def run_command(args: argparse.Namespace):
    """Despacha o comando selecionado para o handler correspondente."""

    HANDLERS[args.comando](args)


def main(argv: list[str] | None = None):
    """Inicializa a CLI, interpreta argumentos e executa o comando selecionado."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        run_command(args)
    except UserInputError as exc:
        logger.error("%s", exc)
        sys.exit(2)
    except Exception:
        logger.exception("A execução falhou:")
        sys.exit(1)


__all__ = [
    "COMMANDS",
    "HANDLERS",
    "build_parser",
    "main",
    "parse_data_iso",
    "run_command",
]
