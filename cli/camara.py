"""Comandos da CLI relacionados a Camara e CSVs."""

from __future__ import annotations

import argparse

from configuracao import obter_parametros_cli

from .comun import CliCommand
from .comun import adicionar_args_intervalo_anos


def _configurar_gerar_csv(parser: argparse.ArgumentParser):
    """Configura argumentos do gerador de CSVs."""

    config = obter_parametros_cli("gerar_csv")
    parser.add_argument(
        "--data-dir",
        default=config.get("data_dir"),
        help="Diretório raiz dos dados.",
    )
    parser.add_argument(
        "--output-dir",
        default=config.get("output_dir"),
        help="Diretório raiz onde os CSVs serão salvos.",
    )


def _configurar_extrair_dependentes(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator de dados dependentes da Camara."""

    parser.add_argument("--endpoint", required=True, help="Nome do endpoint no config.")
    adicionar_args_intervalo_anos(parser)


def _configurar_rodar_pipeline(parser: argparse.ArgumentParser):
    """Configura overrides do pipeline da Camara."""

    adicionar_args_intervalo_anos(parser, usar_defaults_compartilhados=False)


def handle_gerar_csv(args: argparse.Namespace):
    """Executa todos os geradores de CSV registrados no projeto."""

    from utils.csv.orquestrador_csv import OrquestradorGeracaoCSVs

    OrquestradorGeracaoCSVs(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    ).executar()


def handle_rodar_pipeline(args: argparse.Namespace):
    """Executa o pipeline completo da Camara."""

    from pipeline import PipelineCamara

    PipelineCamara(ano_inicio=args.ano_inicio, ano_fim=args.ano_fim).executar()


def handle_baixar_legislaturas(_: argparse.Namespace):
    """Baixa a lista base de legislaturas da Camara."""

    from extracao.camara.deputados_federais import Legislatura

    Legislatura().executar()


def handle_extrair_legislaturas(_: argparse.Namespace):
    """Expande os deputados associados a cada legislatura."""

    from extracao.camara.deputados_federais import DeputadosLegislatura

    DeputadosLegislatura().executar()


def handle_extrair_dependentes(args: argparse.Namespace):
    """Extrai dados dependentes da Camara, como despesas."""

    from configuracao import obter_configuracao_endpoint
    from extracao.camara.deputados_federais import Despesas

    config = obter_configuracao_endpoint(args.endpoint)
    Despesas(args.endpoint, config).executar(
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
    )


COMMANDS: tuple[CliCommand, ...] = (
    CliCommand(
        name="gerar-csv",
        help="Executa todos os geradores de CSV registrados no projeto.",
        handler=handle_gerar_csv,
        configure_parser=_configurar_gerar_csv,
    ),
    CliCommand(
        name="extrair-legislaturas",
        help="Extrai os deputados vinculados às legislaturas.",
        handler=handle_extrair_legislaturas,
    ),
    CliCommand(
        name="baixar-legislaturas",
        help="Baixa o arquivo base com IDs de legislaturas.",
        handler=handle_baixar_legislaturas,
    ),
    CliCommand(
        name="extrair-dependentes",
        help="Extrai dados dependentes (ex: despesas).",
        handler=handle_extrair_dependentes,
        configure_parser=_configurar_extrair_dependentes,
    ),
    CliCommand(
        name="rodar-pipeline",
        help="Executa o pipeline completo da Câmara.",
        handler=handle_rodar_pipeline,
        configure_parser=_configurar_rodar_pipeline,
    ),
)
