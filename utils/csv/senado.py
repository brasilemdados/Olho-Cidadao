"""Geracao da camada analitica do Senado."""

from __future__ import annotations

from pathlib import Path

from .comum import FonteObrigatoria
from .comum import escrever_csv
from .comum import hash_id
from .comum import id_competencia
from .comum import id_tempo
from .comum import id_tipo_despesa
from .comum import id_tipo_documento_fiscal
from .comum import iterar_registros_em_arquivos
from .comum import ordenar_numero_texto

ARQUIVO_DIM_SENADORES = "dim_senadores.csv"
ARQUIVO_TB_DOCUMENTOS = "tb_documentos_despesas_senadores.csv"
ARQUIVO_FATO_DESPESAS = "tb_despesas_senadores.csv"

FONTES_OBRIGATORIAS = (
    FonteObrigatoria("senadores/ceaps_*.json", "despesas CEAPS do Senado"),
)


def _caminhos_despesas(data_dir: Path) -> list[Path]:
    return sorted((data_dir / "senadores").glob("ceaps_*.json"))


def iterar_registros_despesa_senado(data_dir: Path):
    """Itera as despesas do Senado com chaves analiticas derivadas."""

    for registro in iterar_registros_em_arquivos(_caminhos_despesas(data_dir)):
        id_documento = hash_id(
            "documento_senado",
            registro.get("documento_fornecedor_normalizado") or registro.get("cpfCnpj"),
            registro.get("tipoDocumento"),
            registro.get("data_documento") or registro.get("data"),
            registro.get("documento"),
            registro.get("detalhamento"),
        )
        yield {
            **registro,
            "id_documento_despesa": id_documento,
            "id_tempo_documento": id_tempo(
                registro.get("data_documento") or registro.get("data")
            ),
            "id_competencia": id_competencia(registro.get("ano"), registro.get("mes")),
            "id_tipo_despesa": id_tipo_despesa("senado", registro.get("tipoDespesa")),
            "id_tipo_documento_fiscal": id_tipo_documento_fiscal(
                "senado",
                None,
                registro.get("tipoDocumento"),
            ),
        }


def _linhas_dim_senadores(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_registros_despesa_senado(data_dir):
        codigo = registro.get("codSenador")
        if codigo in registros:
            continue
        registros[codigo] = [codigo, registro.get("nomeSenador")]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_documentos(data_dir: Path) -> list[list[object]]:
    registros: dict[str, list[object]] = {}

    for registro in iterar_registros_despesa_senado(data_dir):
        chave = registro["id_documento_despesa"]
        if chave in registros:
            continue
        registros[chave] = [
            chave,
            registro.get("documento_fornecedor_normalizado"),
            registro.get("id_tipo_documento_fiscal"),
            registro.get("id_tempo_documento"),
            registro.get("documento"),
            registro.get("detalhamento"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_despesas(data_dir: Path) -> list[list[object]]:
    linhas = []

    for registro in iterar_registros_despesa_senado(data_dir):
        linhas.append(
            [
                registro.get("id_despesa_senado") or registro.get("id"),
                registro.get("id_documento_despesa"),
                registro.get("codSenador"),
                registro.get("id_tipo_despesa"),
                registro.get("id_competencia"),
                registro.get("valorReembolsado"),
            ]
        )

    return linhas


def gerar_csvs_senado(data_dir: Path, output_dir: Path) -> list[str]:
    """Gera dimensao e fato de despesas do Senado."""

    escrever_csv(
        output_dir / ARQUIVO_DIM_SENADORES,
        ("id_senador", "nome_senador"),
        _linhas_dim_senadores(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_TB_DOCUMENTOS,
        (
            "id_documento_despesa",
            "id_fornecedor",
            "id_tipo_documento_fiscal",
            "id_tempo_documento",
            "numero_documento",
            "detalhamento",
        ),
        _linhas_documentos(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_FATO_DESPESAS,
        (
            "id_despesa_senador",
            "id_documento_despesa",
            "id_senador",
            "id_tipo_despesa",
            "id_competencia",
            "valor_reembolsado",
        ),
        _linhas_despesas(data_dir),
    )
    return [ARQUIVO_DIM_SENADORES, ARQUIVO_TB_DOCUMENTOS, ARQUIVO_FATO_DESPESAS]
