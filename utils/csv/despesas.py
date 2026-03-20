"""Dimensoes compartilhadas entre as despesas da Camara e do Senado."""

from __future__ import annotations

from pathlib import Path

from .camara import FONTES_OBRIGATORIAS as FONTES_CAMARA
from .camara import iterar_registros_despesa_camara
from .comum import FonteObrigatoria
from .comum import escrever_csv
from .comum import id_competencia
from .comum import id_tempo
from .comum import id_tipo_despesa
from .comum import id_tipo_documento_fiscal
from .senado import FONTES_OBRIGATORIAS as FONTES_SENADO
from .senado import iterar_registros_despesa_senado

ARQUIVO_DIM_TEMPO = "dim_tempo.csv"
ARQUIVO_DIM_COMPETENCIA = "dim_competencia_mensal.csv"
ARQUIVO_DIM_TIPOS_DOCUMENTO = "dim_tipos_documento_fiscal.csv"
ARQUIVO_DIM_TIPOS_DESPESA = "dim_tipos_despesa.csv"

FONTES_OBRIGATORIAS: tuple[FonteObrigatoria, ...] = (
    *FONTES_CAMARA,
    *FONTES_SENADO,
)


def _iterar_registros(data_dir: Path):
    yield from iterar_registros_despesa_camara(data_dir)
    yield from iterar_registros_despesa_senado(data_dir)


def _linhas_tempo(data_dir: Path) -> list[list[object]]:
    registros: dict[str, list[object]] = {}

    for registro in _iterar_registros(data_dir):
        chave = id_tempo(registro.get("data_documento") or registro.get("dataDocumento"))
        if not chave or chave in registros:
            continue
        ano, mes, dia = chave.split("-")
        registros[chave] = [chave, chave, ano, mes, dia]

    return [registros[chave] for chave in sorted(registros)]


def _linhas_competencia(data_dir: Path) -> list[list[object]]:
    registros: dict[str, list[object]] = {}

    for registro in _iterar_registros(data_dir):
        chave = id_competencia(registro.get("ano"), registro.get("mes"))
        if not chave or chave in registros:
            continue
        ano, mes = chave.split("-")
        registros[chave] = [chave, ano, mes]

    return [registros[chave] for chave in sorted(registros)]


def _linhas_tipos_documento(data_dir: Path) -> list[list[object]]:
    registros: dict[str, list[object]] = {}

    for origem, iterador in (
        ("camara", iterar_registros_despesa_camara(data_dir)),
        ("senado", iterar_registros_despesa_senado(data_dir)),
    ):
        for registro in iterador:
            codigo = registro.get("codTipoDocumento") if origem == "camara" else None
            nome = registro.get("tipoDocumento")
            chave = id_tipo_documento_fiscal(origem, codigo, nome)
            if chave in registros:
                continue
            registros[chave] = [chave, origem, codigo, nome]

    return [registros[chave] for chave in sorted(registros)]


def _linhas_tipos_despesa(data_dir: Path) -> list[list[object]]:
    registros: dict[str, list[object]] = {}

    for origem, iterador in (
        ("camara", iterar_registros_despesa_camara(data_dir)),
        ("senado", iterar_registros_despesa_senado(data_dir)),
    ):
        for registro in iterador:
            nome = registro.get("tipoDespesa")
            chave = id_tipo_despesa(origem, nome)
            if chave in registros:
                continue
            registros[chave] = [chave, origem, nome]

    return [
        registros[chave]
        for chave in sorted(registros, key=lambda valor: (valor.split(":", maxsplit=1)[0], valor))
    ]


def gerar_csvs_despesas_compartilhadas(data_dir: Path, output_dir: Path) -> list[str]:
    """Gera dimensoes comuns as duas casas legislativas."""

    escrever_csv(
        output_dir / ARQUIVO_DIM_TEMPO,
        ("id_tempo", "data", "ano", "mes", "dia"),
        _linhas_tempo(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_COMPETENCIA,
        ("id_competencia", "ano", "mes"),
        _linhas_competencia(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_TIPOS_DOCUMENTO,
        (
            "id_tipo_documento_fiscal",
            "origem",
            "codigo_tipo_documento",
            "tipo_documento_fiscal",
        ),
        _linhas_tipos_documento(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_TIPOS_DESPESA,
        ("id_tipo_despesa", "origem", "tipo_despesa"),
        _linhas_tipos_despesa(data_dir),
    )
    return [
        ARQUIVO_DIM_TEMPO,
        ARQUIVO_DIM_COMPETENCIA,
        ARQUIVO_DIM_TIPOS_DOCUMENTO,
        ARQUIVO_DIM_TIPOS_DESPESA,
    ]
