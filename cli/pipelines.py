"""Comandos de orquestracao entre multiplas fontes."""

from __future__ import annotations

import argparse

from .comun import CliCommand
from .comun import adicionar_args_intervalo_anos
from .comun import adicionar_flag_inclusao
from .comun import parse_data_iso


def _configurar_rodar_paralelo(parser: argparse.ArgumentParser):
    """Configura argumentos do pipeline paralelo."""

    adicionar_args_intervalo_anos(
        parser,
        usar_defaults_compartilhados=False,
    )
    parser.add_argument(
        "--pncp-data-inicial",
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    parser.add_argument(
        "--pncp-data-final",
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    for nome, destino, descricao in (
        ("camara", "incluir_camara", "a fonte Camara"),
        ("senado", "incluir_senado", "a fonte Senado"),
        ("siop", "incluir_siop", "a fonte SIOP"),
        ("ibge", "incluir_ibge", "a fonte IBGE"),
        ("pncp", "incluir_pncp", "a fonte PNCP"),
        ("transferegov", "incluir_transferegov", "a fonte Transferegov"),
        ("obrasgov", "incluir_obrasgov", "a fonte ObrasGov"),
        ("siconfi", "incluir_siconfi", "a fonte Siconfi"),
    ):
        adicionar_flag_inclusao(
            parser,
            nome=nome,
            destino=destino,
            descricao=descricao,
        )


def _configurar_rodar_pipeline_completo(parser: argparse.ArgumentParser):
    """Configura argumentos do pipeline completo."""

    parser.add_argument("--ano-inicio", type=int, default=None)
    parser.add_argument(
        "--ano-fim",
        type=int,
        default=None,
        help="Ano final exclusivo. Se omitido, usa a configuração do pipeline.",
    )
    parser.add_argument("--max-workers", type=int, default=None)
    for nome, destino, descricao in (
        (
            "portal",
            "incluir_portal",
            "o enriquecimento do Portal da Transparencia",
        ),
        ("anp", "incluir_anp", "o enriquecimento da ANP"),
        (
            "obrasgov-geometrias",
            "incluir_obrasgov_geometrias",
            "as geometrias do ObrasGov",
        ),
    ):
        adicionar_flag_inclusao(
            parser,
            nome=nome,
            destino=destino,
            descricao=descricao,
        )


def handle_rodar_paralelo(args: argparse.Namespace):
    """Executa as fontes independentes em paralelo controlado."""

    from pipeline import PipelineParalelo

    PipelineParalelo(
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        pncp_data_inicial=(
            parse_data_iso(args.pncp_data_inicial) if args.pncp_data_inicial else None
        ),
        pncp_data_final=(
            parse_data_iso(args.pncp_data_final) if args.pncp_data_final else None
        ),
        max_workers=args.max_workers,
        incluir_camara=args.incluir_camara,
        incluir_senado=args.incluir_senado,
        incluir_siop=args.incluir_siop,
        incluir_ibge=args.incluir_ibge,
        incluir_pncp=args.incluir_pncp,
        incluir_transferegov=args.incluir_transferegov,
        incluir_obrasgov=args.incluir_obrasgov,
        incluir_siconfi=args.incluir_siconfi,
    ).executar()


def handle_rodar_pipeline_completo(args: argparse.Namespace):
    """Executa o pipeline completo configurado no `etl-config.toml`."""

    from pipeline import PipelineCompleto

    PipelineCompleto(
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        max_workers=args.max_workers,
        incluir_portal=args.incluir_portal,
        incluir_anp=args.incluir_anp,
        incluir_obrasgov_geometrias=args.incluir_obrasgov_geometrias,
    ).executar()


COMMANDS: tuple[CliCommand, ...] = (
    CliCommand(
        name="rodar-paralelo",
        help="Executa em paralelo as extrações que não dependem umas das outras.",
        handler=handle_rodar_paralelo,
        configure_parser=_configurar_rodar_paralelo,
    ),
    CliCommand(
        name="rodar-pipeline-completo",
        help="Executa a extração completa em fases, usando a configuração do etl-config.toml.",
        handler=handle_rodar_pipeline_completo,
        configure_parser=_configurar_rodar_pipeline_completo,
    ),
)
