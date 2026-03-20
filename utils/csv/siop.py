"""Geracao das dimensoes analiticas derivadas do SIOP."""

from __future__ import annotations

from pathlib import Path

from .comum import FonteObrigatoria
from .comum import escrever_csv
from .comum import hash_id
from .comum import iterar_registros_em_arquivos
from .comum import ordenar_numero_texto

ARQUIVO_DIM_FUNCOES = "dim_funcao_siop.csv"
ARQUIVO_DIM_SUBFUNCOES = "dim_subfuncao_siop.csv"
ARQUIVO_DIM_PROGRAMAS = "dim_programa.csv"
ARQUIVO_DIM_ACOES = "dim_acao_siop.csv"
ARQUIVO_DIM_UNIDADES = "dim_unidades_orcamentarias.csv"
ARQUIVO_DIM_FONTES = "dim_fontes_recurso.csv"
ARQUIVO_DIM_GNDS = "dim_gnds.csv"
ARQUIVO_DIM_MODALIDADES = "dim_modalidades_aplicacao.csv"
ARQUIVO_DIM_ELEMENTOS = "dim_elementos_despesa.csv"
ARQUIVO_TB_EXECUCAO = "tb_execucao_orcamentaria.csv"

FONTES_OBRIGATORIAS = (
    FonteObrigatoria(
        "orcamento_item_despesa/orcamento_item_despesa_*.json",
        "itens de despesa do SIOP",
    ),
)


def _caminhos_itens(data_dir: Path) -> list[Path]:
    return sorted((data_dir / "orcamento_item_despesa").glob("orcamento_item_despesa_*.json"))


def iterar_itens_siop(data_dir: Path):
    """Itera os itens orcamentarios com uma chave estável do item."""

    for registro in iterar_registros_em_arquivos(_caminhos_itens(data_dir)):
        id_item = registro.get("id_item_despesa")
        if not id_item:
            id_item = hash_id("item_siop", registro.get("uri_item"), registro.get("ano"))
        yield {**registro, "id_item_despesa": id_item}


def _linhas_funcoes(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        codigo = registro.get("codigo_funcao")
        if codigo in registros:
            continue
        registros[codigo] = [codigo, registro.get("funcao")]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_subfuncoes(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        codigo = registro.get("codigo_subfuncao")
        if codigo in registros:
            continue
        registros[codigo] = [
            codigo,
            registro.get("subfuncao"),
            registro.get("codigo_funcao"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_programas(data_dir: Path) -> list[list[object]]:
    registros: dict[tuple[object, object], list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        chave = (registro.get("ano"), registro.get("codigo_programa"))
        if chave in registros:
            continue
        registros[chave] = [
            registro.get("ano"),
            registro.get("codigo_programa"),
            registro.get("programa"),
        ]

    return [
        registros[chave]
        for chave in sorted(
            registros,
            key=lambda item: (
                ordenar_numero_texto(item[0]),
                ordenar_numero_texto(item[1]),
            ),
        )
    ]


def _linhas_acoes(data_dir: Path) -> list[list[object]]:
    registros: dict[tuple[object, object], list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        chave = (registro.get("ano"), registro.get("codigo_acao"))
        if chave in registros:
            continue
        registros[chave] = [
            registro.get("ano"),
            registro.get("codigo_acao"),
            registro.get("acao"),
            registro.get("codigo_programa"),
            registro.get("codigo_subfuncao"),
        ]

    return [
        registros[chave]
        for chave in sorted(
            registros,
            key=lambda item: (
                ordenar_numero_texto(item[0]),
                ordenar_numero_texto(item[1]),
            ),
        )
    ]


def _linhas_unidades(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        codigo = registro.get("codigo_unidade_orcamentaria")
        if codigo in registros:
            continue
        registros[codigo] = [codigo, registro.get("unidade_orcamentaria")]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_fontes(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        codigo = registro.get("codigo_fonte")
        if codigo in registros:
            continue
        registros[codigo] = [codigo, registro.get("fonte")]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_gnds(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        codigo = registro.get("codigo_gnd")
        if codigo in registros:
            continue
        registros[codigo] = [codigo, registro.get("gnd")]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_modalidades(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        codigo = registro.get("codigo_modalidade")
        if codigo in registros:
            continue
        registros[codigo] = [codigo, registro.get("modalidade")]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_elementos(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_itens_siop(data_dir):
        codigo = registro.get("codigo_elemento")
        if codigo in registros:
            continue
        registros[codigo] = [codigo, registro.get("elemento"), registro.get("codigo_gnd")]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_execucao(data_dir: Path) -> list[list[object]]:
    linhas = []

    for registro in iterar_itens_siop(data_dir):
        linhas.append(
            [
                registro.get("id_item_despesa"),
                registro.get("ano"),
                registro.get("codigo_subfuncao"),
                registro.get("codigo_programa"),
                registro.get("codigo_acao"),
                registro.get("codigo_unidade_orcamentaria"),
                registro.get("codigo_fonte"),
                registro.get("codigo_gnd"),
                registro.get("codigo_modalidade"),
                registro.get("codigo_elemento"),
                registro.get("valor_pago"),
                registro.get("valor_empenhado"),
                registro.get("valor_liquidado"),
            ]
        )

    return linhas


def gerar_csvs_siop(data_dir: Path, output_dir: Path) -> list[str]:
    """Gera as dimensoes de classificacao e o fato do SIOP."""

    escrever_csv(
        output_dir / ARQUIVO_DIM_FUNCOES,
        ("codigo_funcao", "funcao"),
        _linhas_funcoes(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_SUBFUNCOES,
        ("codigo_subfuncao", "subfuncao", "codigo_funcao"),
        _linhas_subfuncoes(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_PROGRAMAS,
        ("ano", "codigo_programa", "programa"),
        _linhas_programas(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_ACOES,
        ("ano", "codigo_acao", "acao", "codigo_programa", "codigo_subfuncao"),
        _linhas_acoes(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_UNIDADES,
        ("codigo_unidade_orcamentaria", "unidade_orcamentaria"),
        _linhas_unidades(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_FONTES,
        ("codigo_fonte", "fonte_recurso"),
        _linhas_fontes(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_GNDS,
        ("codigo_gnd", "grupo_natureza_despesa"),
        _linhas_gnds(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_MODALIDADES,
        ("codigo_modalidade", "modalidade_aplicacao"),
        _linhas_modalidades(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_ELEMENTOS,
        ("codigo_elemento", "elemento_despesa", "codigo_gnd"),
        _linhas_elementos(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_TB_EXECUCAO,
        (
            "id_item_despesa",
            "ano",
            "codigo_subfuncao",
            "codigo_programa",
            "codigo_acao",
            "codigo_unidade_orcamentaria",
            "codigo_fonte",
            "codigo_gnd",
            "codigo_modalidade",
            "codigo_elemento",
            "valor_pago",
            "valor_empenhado",
            "valor_liquidado",
        ),
        _linhas_execucao(data_dir),
    )
    return [
        ARQUIVO_DIM_FUNCOES,
        ARQUIVO_DIM_SUBFUNCOES,
        ARQUIVO_DIM_PROGRAMAS,
        ARQUIVO_DIM_ACOES,
        ARQUIVO_DIM_UNIDADES,
        ARQUIVO_DIM_FONTES,
        ARQUIVO_DIM_GNDS,
        ARQUIVO_DIM_MODALIDADES,
        ARQUIVO_DIM_ELEMENTOS,
        ARQUIVO_TB_EXECUCAO,
    ]
