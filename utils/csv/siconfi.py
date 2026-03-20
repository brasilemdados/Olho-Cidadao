"""Geracao da dimensao de entes do Siconfi."""

from __future__ import annotations

from pathlib import Path

from .comum import FonteObrigatoria
from .comum import escrever_csv
from .comum import iterar_registros_json
from .comum import ordenar_numero_texto

ARQUIVO_DIM_ENTES = "dim_entes.csv"

FONTES_OBRIGATORIAS = (
    FonteObrigatoria("siconfi/entes/consulta=all.json", "cadastro de entes do Siconfi"),
)


def _linhas_entes(data_dir: Path) -> list[list[object]]:
    registros: dict[object, tuple[object, list[object]]] = {}

    for registro in iterar_registros_json(data_dir / "siconfi" / "entes" / "consulta=all.json"):
        payload = registro.get("payload") or {}
        codigo = payload.get("cod_ibge")
        exercicio = payload.get("exercicio") or 0
        atual = [
            codigo,
            payload.get("ente"),
            payload.get("uf"),
            payload.get("esfera"),
            payload.get("capital"),
            payload.get("populacao"),
            payload.get("cnpj"),
        ]

        anterior = registros.get(codigo)
        if anterior is None or exercicio >= anterior[0]:
            registros[codigo] = (exercicio, atual)

    return [registros[chave][1] for chave in sorted(registros, key=ordenar_numero_texto)]


def gerar_csvs_siconfi(data_dir: Path, output_dir: Path) -> list[str]:
    """Gera a dimensao analitica de entes sem atributos redundantes."""

    escrever_csv(
        output_dir / ARQUIVO_DIM_ENTES,
        (
            "id_ente",
            "nome_ente",
            "sigla_uf",
            "esfera",
            "capital",
            "populacao",
            "cnpj",
        ),
        _linhas_entes(data_dir),
    )
    return [ARQUIVO_DIM_ENTES]
