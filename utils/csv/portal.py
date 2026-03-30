"""Geracao da dimensao analitica de fornecedores observados localmente."""

from __future__ import annotations

from pathlib import Path

from extracao.portal import ConstrutorDimFornecedoresPortal

from .comum import escrever_csv
from .comum import iterar_registros_json

ARQUIVO_DIM_FORNECEDORES = "dim_fornecedores.csv"


def _caminho_dimensao_fornecedores(data_dir: Path) -> Path:
    return data_dir / "portal_transparencia" / "dimensoes" / "fornecedores.jsonl"


def _linhas_fornecedores(caminho_dimensao: Path) -> list[list[object]]:
    linhas = []

    for registro in iterar_registros_json(caminho_dimensao):
        linhas.append(
            [
                registro.get("documento"),
                registro.get("documento"),
                registro.get("tipo_documento"),
                registro.get("cnpj_base"),
                registro.get("nome_principal"),
            ]
        )

    return linhas


def gerar_csvs_portal(data_dir: Path, output_dir: Path) -> list[str]:
    """Reconstrui a dimensao local de fornecedores e exporta o CSV final."""

    caminho_dimensao = _caminho_dimensao_fornecedores(data_dir)
    ConstrutorDimFornecedoresPortal(
        output_path=caminho_dimensao,
        diretorio_camara=data_dir / "despesas_deputados_federais",
        diretorio_senado=data_dir / "senadores",
    ).construir()

    escrever_csv(
        output_dir / ARQUIVO_DIM_FORNECEDORES,
        (
            "id_fornecedor",
            "documento",
            "tipo_documento",
            "cnpj_base",
            "nome_principal",
        ),
        _linhas_fornecedores(caminho_dimensao),
    )
    return [ARQUIVO_DIM_FORNECEDORES]
