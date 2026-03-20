"""Comandos da CLI para o Portal da Transparencia."""

from __future__ import annotations

import argparse

from configuracao import obter_parametros_cli

from .comun import CliCommand
from .comun import adicionar_arg_limit_fornecedores
from .comun import adicionar_arg_min_ocorrencias


def _obter_config_portal() -> dict:
    """Retorna a configuracao base da CLI do Portal."""

    return obter_parametros_cli("portal")


def _configurar_min_ocorrencias(parser: argparse.ArgumentParser):
    """Adiciona apenas o argumento de minimo de ocorrencias."""

    adicionar_arg_min_ocorrencias(
        parser,
        default=_obter_config_portal().get("min_ocorrencias"),
    )


def _configurar_portal_documentos(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator de documentos do Portal."""

    config = _obter_config_portal()
    adicionar_arg_min_ocorrencias(parser, default=config.get("min_ocorrencias"))
    adicionar_arg_limit_fornecedores(parser)
    parser.add_argument("--ano-inicio", type=int, default=None)
    parser.add_argument(
        "--ano-fim",
        type=int,
        default=None,
        help="Ano final exclusivo para documentos por favorecido.",
    )
    parser.add_argument(
        "--fases",
        type=int,
        nargs="*",
        default=config.get("fases"),
        help="Fases para consultar no endpoint documentos-por-favorecido.",
    )


def _configurar_portal_simples(parser: argparse.ArgumentParser):
    """Configura argumentos comuns a sancoes e notas fiscais do Portal."""

    adicionar_arg_min_ocorrencias(
        parser,
        default=_obter_config_portal().get("min_ocorrencias"),
    )
    adicionar_arg_limit_fornecedores(parser)


def handle_portal_construir_fornecedores(args: argparse.Namespace):
    """Reconstrói a dimensão local de fornecedores do Portal."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(min_ocorrencias=args.min_ocorrencias).executar_dimensao()


def handle_extrair_portal_documentos(args: argparse.Namespace):
    """Extrai documentos por favorecido do Portal da Transparência."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        fases=args.fases,
    ).executar_documentos()


def handle_extrair_portal_sancoes(args: argparse.Namespace):
    """Extrai CEIS, CNEP e CEPIM para os fornecedores selecionados."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
    ).executar_sancoes()


def handle_extrair_portal_notas_fiscais(args: argparse.Namespace):
    """Extrai notas fiscais do Portal da Transparência."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
    ).executar_notas_fiscais()


def handle_rodar_pipeline_portal(args: argparse.Namespace):
    """Executa a pipeline completa do Portal da Transparência."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        fases=args.fases,
    ).executar()


COMMANDS: tuple[CliCommand, ...] = (
    CliCommand(
        name="portal-construir-fornecedores",
        help=(
            "Constrói a dimensão de fornecedores para enriquecimento com o "
            "Portal da Transparência."
        ),
        handler=handle_portal_construir_fornecedores,
        configure_parser=_configurar_min_ocorrencias,
    ),
    CliCommand(
        name="extrair-portal-documentos",
        help="Extrai documentos por favorecido do Portal da Transparência.",
        handler=handle_extrair_portal_documentos,
        configure_parser=_configurar_portal_documentos,
    ),
    CliCommand(
        name="extrair-portal-sancoes",
        help="Extrai CEIS, CNEP e CEPIM para os fornecedores encontrados no projeto.",
        handler=handle_extrair_portal_sancoes,
        configure_parser=_configurar_portal_simples,
    ),
    CliCommand(
        name="extrair-portal-notas-fiscais",
        help="Extrai notas fiscais do Portal da Transparência por CNPJ emitente.",
        handler=handle_extrair_portal_notas_fiscais,
        configure_parser=_configurar_portal_simples,
    ),
    CliCommand(
        name="rodar-pipeline-portal",
        help="Executa a pipeline completa de enriquecimento com o Portal da Transparência.",
        handler=handle_rodar_pipeline_portal,
        configure_parser=_configurar_portal_documentos,
    ),
)
