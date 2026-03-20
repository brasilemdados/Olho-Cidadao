"""Comandos de interface e operacao local da CLI."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from .comun import CliCommand


def _binario_cidadao_de_olho(app_dir: Path, release: bool) -> Path:
    """Resolve o caminho do binario compilado do app web."""

    perfil = "release" if release else "debug"
    return app_dir / "target" / perfil / "cidadao_de_olho-cli"


def _binario_cidadao_de_olho_esta_atualizado(app_dir: Path, binario: Path) -> bool:
    """Verifica se o binario e mais novo do que as fontes Rust do app."""

    if not binario.exists():
        return False

    referencias = [
        app_dir / "Cargo.toml",
        app_dir / "Cargo.lock",
        *sorted((app_dir / "src").rglob("*.rs")),
    ]
    instante_referencia = max(
        caminho.stat().st_mtime for caminho in referencias if caminho.exists()
    )
    return binario.stat().st_mtime >= instante_referencia


def _configurar_servir_cidadao_de_olho(parser: argparse.ArgumentParser):
    """Configura argumentos do app web publico."""

    parser.add_argument(
        "--ambiente",
        choices=["development", "production", "test"],
        default="development",
        help="Perfil de configuracao do app Loco.rs.",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Compila e executa o app web em modo release.",
    )


def handle_menu(_: argparse.Namespace):
    """Abre o menu interativo do terminal."""

    from .menu import open_terminal_menu

    open_terminal_menu()


def handle_servir_cidadao_de_olho(args: argparse.Namespace):
    """Sobe a aplicacao publica Olho Cidadão baseada em Loco.rs."""

    from configuracao import PROJECT_ROOT

    app_dir = PROJECT_ROOT / "apps" / "cidadao_de_olho"
    manifest_path = app_dir / "Cargo.toml"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Aplicacao Loco.rs nao encontrada em {manifest_path}."
        )

    ambiente = os.environ.copy()
    ambiente["LOCO_ENV"] = args.ambiente
    binario = _binario_cidadao_de_olho(app_dir, args.release)

    try:
        if not _binario_cidadao_de_olho_esta_atualizado(app_dir, binario):
            comando_build = ["cargo", "build", "--manifest-path", str(manifest_path)]
            if args.release:
                comando_build.append("--release")

            subprocess.run(
                comando_build,
                cwd=app_dir,
                env=ambiente,
                check=True,
            )

        subprocess.run(
            [str(binario), "start"],
            cwd=app_dir,
            env=ambiente,
            check=True,
        )
    except KeyboardInterrupt:
        return


COMMANDS: tuple[CliCommand, ...] = (
    CliCommand(
        name="menu",
        aliases=("abrir-menu",),
        help="Abre um menu interativo para navegar pelas funcionalidades da CLI.",
        handler=handle_menu,
    ),
    CliCommand(
        name="servir-cidadao-de-olho",
        aliases=("abrir-cidadao-de-olho",),
        help="Inicia a aplicacao publica Olho Cidadão em Loco.rs.",
        handler=handle_servir_cidadao_de_olho,
        configure_parser=_configurar_servir_cidadao_de_olho,
    ),
)
