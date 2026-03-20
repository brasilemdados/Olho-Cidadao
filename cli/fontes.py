"""Comandos da CLI para fontes complementares e APIs publicas."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from configuracao import obter_parametros_cli
from configuracao import resolver_data_configurada_iso

from .comun import CliCommand
from .comun import adicionar_arg_filtros
from .comun import adicionar_arg_limit_fornecedores
from .comun import adicionar_arg_min_ocorrencias
from .comun import adicionar_arg_tamanho_pagina
from .comun import parse_data_iso


def _configurar_extrair_senado(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator do Senado."""

    config = obter_parametros_cli("extrair_senado")
    parser.add_argument(
        "--endpoint",
        default=config.get("endpoint"),
        help="Nome do endpoint no config (padrão: ceaps).",
    )


def _configurar_extrair_ibge(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator de localidades do IBGE."""

    from extracao.ibge import IBGE_DATASETS

    config = obter_parametros_cli("extrair_ibge_localidades")
    parser.add_argument(
        "--datasets",
        nargs="*",
        choices=list(IBGE_DATASETS),
        default=config.get("datasets"),
    )


def _configurar_extrair_pncp(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator do PNCP."""

    config = obter_parametros_cli("extrair_pncp")
    parser.add_argument(
        "--data-inicial",
        default=resolver_data_configurada_iso(config.get("data_inicial")),
    )
    parser.add_argument(
        "--data-final",
        default=resolver_data_configurada_iso(config.get("data_final")),
    )
    adicionar_arg_tamanho_pagina(parser, default=config.get("tamanho_pagina"))
    parser.add_argument("--codigo-classificacao-superior", default=None)
    parser.add_argument("--sem-contratos", action="store_true")
    parser.add_argument("--sem-atas", action="store_true")
    parser.add_argument("--sem-pca", action="store_true")


def _configurar_extrair_obrasgov(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator do ObrasGov."""

    from extracao.obrasgov import PAGEABLE_RESOURCES

    config = obter_parametros_cli("extrair_obrasgov")
    parser.add_argument(
        "--recursos",
        nargs="*",
        choices=list(PAGEABLE_RESOURCES),
        default=None,
    )
    adicionar_arg_filtros(parser)
    adicionar_arg_tamanho_pagina(parser, default=config.get("tamanho_pagina"))


def _configurar_extrair_obrasgov_geometrias(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator de geometrias do ObrasGov."""

    parser.add_argument("--limit-ids", type=int, default=None)


def _configurar_extrair_siconfi(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator do Siconfi."""

    from extracao.siconfi import SICONFI_RESOURCES

    config = obter_parametros_cli("extrair_siconfi")
    parser.add_argument(
        "--recursos",
        nargs="*",
        choices=list(SICONFI_RESOURCES),
        default=config.get("recursos"),
    )
    adicionar_arg_filtros(
        parser,
        help=(
            "Filtro no formato chave=valor. Pode ser repetido. "
            "Recursos como extrato_entregas, msc_*, rreo, rgf e dca "
            "exigem filtros obrigatórios específicos."
        ),
    )
    adicionar_arg_tamanho_pagina(parser, default=config.get("tamanho_pagina"))


def _configurar_extrair_anp(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator da ANP."""

    from extracao.anp import ANP_DATASETS

    config = obter_parametros_cli("extrair_anp")
    parser.add_argument(
        "--datasets",
        nargs="*",
        choices=list(ANP_DATASETS),
        default=config.get("datasets"),
    )
    adicionar_arg_min_ocorrencias(parser, default=config.get("min_ocorrencias"))
    adicionar_arg_limit_fornecedores(parser)


def _configurar_transferegov(grupo: str) -> Callable[[argparse.ArgumentParser], None]:
    """Cria a configuracao de parser para um grupo do Transferegov."""

    def configurar(parser: argparse.ArgumentParser):
        from extracao.transferegov import RESOURCE_GROUPS

        config = obter_parametros_cli("extrair_transferegov")
        parser.add_argument(
            "--recursos",
            nargs="*",
            choices=RESOURCE_GROUPS[grupo],
            default=None,
        )
        adicionar_arg_filtros(parser)
        adicionar_arg_tamanho_pagina(parser, default=config.get("tamanho_pagina"))

    return configurar


def handle_extrair_senado(args: argparse.Namespace):
    """Extrai os dados configurados do Senado."""

    from extracao.senado import DadosSenado

    DadosSenado(args.endpoint).executar()


def handle_extrair_siop(_: argparse.Namespace):
    """Extrai o dataset orçamentário do SIOP."""

    from extracao.siop import SIOP

    SIOP().executar()


def handle_extrair_ibge_localidades(args: argparse.Namespace):
    """Extrai regiões, estados e municípios do IBGE."""

    from extracao.ibge import LocalidadesIBGE

    LocalidadesIBGE().executar(datasets=args.datasets)


def handle_extrair_pncp(args: argparse.Namespace):
    """Extrai contratos, atas e PCA do PNCP."""

    from extracao.pncp import PNCPConsulta

    PNCPConsulta(page_size=args.tamanho_pagina).executar(
        data_inicial=parse_data_iso(args.data_inicial),
        data_final=parse_data_iso(args.data_final),
        incluir_contratos=not args.sem_contratos,
        incluir_atas=not args.sem_atas,
        incluir_pca=not args.sem_pca,
        codigo_classificacao_superior=args.codigo_classificacao_superior,
    )


def _handle_extrair_transferegov(args: argparse.Namespace, grupo: str):
    """Extrai um grupo de recursos do Transferegov."""

    from extracao.transferegov import TransferegovRecursos
    from utils.filtros import parse_filtros_cli

    filtros = parse_filtros_cli(args.filtro)
    TransferegovRecursos(
        grupo=grupo,
        page_size=args.tamanho_pagina,
    ).executar(recursos=args.recursos, filtros=filtros)


def handle_extrair_obrasgov(args: argparse.Namespace):
    """Extrai projetos e execuções do ObrasGov."""

    from extracao.obrasgov import ObrasGov
    from utils.filtros import parse_filtros_cli

    filtros = parse_filtros_cli(args.filtro)
    ObrasGov(page_size=args.tamanho_pagina).executar_recursos(
        recursos=args.recursos,
        filtros=filtros,
    )


def handle_extrair_obrasgov_geometrias(args: argparse.Namespace):
    """Extrai as geometrias de projetos já persistidos no ObrasGov."""

    from extracao.obrasgov import ObrasGov

    ObrasGov().executar_geometrias(limit_ids=args.limit_ids)


def handle_extrair_siconfi(args: argparse.Namespace):
    """Extrai recursos configurados do Siconfi."""

    from extracao.siconfi import preparar_consultas_siconfi
    from utils.filtros import parse_filtros_cli

    filtros = parse_filtros_cli(args.filtro)
    preparar_consultas_siconfi(args.recursos, filtros)

    from extracao.siconfi import Siconfi

    Siconfi(page_size=args.tamanho_pagina).executar(
        recursos=args.recursos,
        filtros=filtros,
    )


def handle_extrair_anp(args: argparse.Namespace):
    """Extrai revendedores ANP a partir da dimensão local de fornecedores."""

    from extracao.anp import RevendedoresANP

    RevendedoresANP(
        min_ocorrencias=args.min_ocorrencias,
        limit_fornecedores=args.limit_fornecedores,
    ).executar(datasets=args.datasets)


def _criar_comando_transferegov(
    *,
    nome: str,
    grupo: str,
    help: str,
) -> CliCommand:
    """Cria um comando do Transferegov sem duplicar handler e parser."""

    return CliCommand(
        name=nome,
        help=help,
        handler=lambda args, grupo=grupo: _handle_extrair_transferegov(args, grupo),
        configure_parser=_configurar_transferegov(grupo),
    )


COMMANDS: tuple[CliCommand, ...] = (
    CliCommand(
        name="extrair-senado",
        help="Extrai dados do Senado Federal (ex: CEAPS).",
        handler=handle_extrair_senado,
        configure_parser=_configurar_extrair_senado,
    ),
    CliCommand(
        name="extrair-siop",
        help="Extrai dados orçamentários do endpoint SPARQL do SIOP.",
        handler=handle_extrair_siop,
    ),
    CliCommand(
        name="extrair-ibge-localidades",
        help="Extrai regiões, estados e municípios da API de localidades do IBGE.",
        handler=handle_extrair_ibge_localidades,
        configure_parser=_configurar_extrair_ibge,
    ),
    CliCommand(
        name="extrair-pncp",
        help="Extrai contratos, atas e PCA da API pública do PNCP.",
        handler=handle_extrair_pncp,
        configure_parser=_configurar_extrair_pncp,
    ),
    _criar_comando_transferegov(
        nome="extrair-transferegov-especial",
        grupo="especial",
        help="Extrai datasets da API de Transferências Especiais do Transferegov.",
    ),
    _criar_comando_transferegov(
        nome="extrair-transferegov-fundo",
        grupo="fundoafundo",
        help="Extrai datasets da API Fundo a Fundo do Transferegov.",
    ),
    _criar_comando_transferegov(
        nome="extrair-transferegov-ted",
        grupo="ted",
        help="Extrai datasets da API TED do Transferegov.",
    ),
    CliCommand(
        name="extrair-obrasgov",
        help="Extrai projetos e execuções da API do ObrasGov.",
        handler=handle_extrair_obrasgov,
        configure_parser=_configurar_extrair_obrasgov,
    ),
    CliCommand(
        name="extrair-obrasgov-geometrias",
        help="Extrai geometrias no ObrasGov para os projetos já persistidos.",
        handler=handle_extrair_obrasgov_geometrias,
        configure_parser=_configurar_extrair_obrasgov_geometrias,
    ),
    CliCommand(
        name="extrair-siconfi",
        help="Extrai recursos da API de dados abertos do Siconfi.",
        handler=handle_extrair_siconfi,
        configure_parser=_configurar_extrair_siconfi,
    ),
    CliCommand(
        name="extrair-anp",
        help="Extrai revendedores autorizados da ANP para os CNPJs do projeto.",
        handler=handle_extrair_anp,
        configure_parser=_configurar_extrair_anp,
    ),
)
