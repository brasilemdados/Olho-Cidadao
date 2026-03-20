"""Geracao das dimensoes geograficas do IBGE em forma normal minima."""

from __future__ import annotations

from pathlib import Path

from .comum import FonteObrigatoria
from .comum import escrever_csv
from .comum import iterar_registros_json
from .comum import ordenar_numero_texto

ARQUIVO_DIM_REGIOES = "dim_regioes.csv"
ARQUIVO_DIM_ESTADOS = "dim_estados.csv"
ARQUIVO_DIM_MESORREGIOES = "dim_mesorregioes.csv"
ARQUIVO_DIM_MICRORREGIOES = "dim_microrregioes.csv"
ARQUIVO_DIM_REGIOES_INTERMEDIARIAS = "dim_regioes_intermediarias.csv"
ARQUIVO_DIM_REGIOES_IMEDIATAS = "dim_regioes_imediatas.csv"
ARQUIVO_DIM_MUNICIPIOS = "dim_municipios.csv"

FONTES_OBRIGATORIAS = (
    FonteObrigatoria("ibge/localidades/regioes.json", "localidades do IBGE: regioes"),
    FonteObrigatoria("ibge/localidades/estados.json", "localidades do IBGE: estados"),
    FonteObrigatoria(
        "ibge/localidades/municipios.json",
        "localidades do IBGE: municipios",
    ),
)


def _payload(registro: dict) -> dict:
    payload = registro.get("payload")
    if isinstance(payload, dict):
        return payload
    return registro


def _caminho_localidades(data_dir: Path, nome: str) -> Path:
    return data_dir / "ibge" / "localidades" / nome


def _linhas_regioes(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_registros_json(_caminho_localidades(data_dir, "regioes.json")):
        payload = _payload(registro)
        registros[payload.get("id")] = [
            payload.get("id"),
            payload.get("sigla"),
            payload.get("nome"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_estados(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_registros_json(_caminho_localidades(data_dir, "estados.json")):
        payload = _payload(registro)
        regiao = payload.get("regiao") or {}
        registros[payload.get("id")] = [
            payload.get("id"),
            payload.get("sigla"),
            payload.get("nome"),
            regiao.get("id"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_mesorregioes(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_registros_json(_caminho_localidades(data_dir, "municipios.json")):
        payload = _payload(registro)
        microrregiao = payload.get("microrregiao") or {}
        mesorregiao = microrregiao.get("mesorregiao") or {}
        uf = mesorregiao.get("UF") or {}
        registros[mesorregiao.get("id")] = [
            mesorregiao.get("id"),
            mesorregiao.get("nome"),
            uf.get("id"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_microrregioes(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_registros_json(_caminho_localidades(data_dir, "municipios.json")):
        payload = _payload(registro)
        microrregiao = payload.get("microrregiao") or {}
        mesorregiao = microrregiao.get("mesorregiao") or {}
        registros[microrregiao.get("id")] = [
            microrregiao.get("id"),
            microrregiao.get("nome"),
            mesorregiao.get("id"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_regioes_intermediarias(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_registros_json(_caminho_localidades(data_dir, "municipios.json")):
        payload = _payload(registro)
        regiao_imediata = payload.get("regiao-imediata") or {}
        regiao_intermediaria = regiao_imediata.get("regiao-intermediaria") or {}
        uf = regiao_intermediaria.get("UF") or {}
        registros[regiao_intermediaria.get("id")] = [
            regiao_intermediaria.get("id"),
            regiao_intermediaria.get("nome"),
            uf.get("id"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_regioes_imediatas(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_registros_json(_caminho_localidades(data_dir, "municipios.json")):
        payload = _payload(registro)
        regiao_imediata = payload.get("regiao-imediata") or {}
        regiao_intermediaria = regiao_imediata.get("regiao-intermediaria") or {}
        registros[regiao_imediata.get("id")] = [
            regiao_imediata.get("id"),
            regiao_imediata.get("nome"),
            regiao_intermediaria.get("id"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def _linhas_municipios(data_dir: Path) -> list[list[object]]:
    registros: dict[object, list[object]] = {}

    for registro in iterar_registros_json(_caminho_localidades(data_dir, "municipios.json")):
        payload = _payload(registro)
        microrregiao = payload.get("microrregiao") or {}
        mesorregiao = microrregiao.get("mesorregiao") or {}
        uf = mesorregiao.get("UF") or {}
        regiao_imediata = payload.get("regiao-imediata") or {}

        registros[payload.get("id")] = [
            payload.get("id"),
            payload.get("nome"),
            uf.get("id"),
            microrregiao.get("id"),
            regiao_imediata.get("id"),
        ]

    return [registros[chave] for chave in sorted(registros, key=ordenar_numero_texto)]


def gerar_csvs_ibge(data_dir: Path, output_dir: Path) -> list[str]:
    """Gera as dimensoes geograficas usadas na analise."""

    escrever_csv(
        output_dir / ARQUIVO_DIM_REGIOES,
        ("id_regiao", "sigla_regiao", "nome_regiao"),
        _linhas_regioes(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_ESTADOS,
        ("id_uf", "sigla_uf", "nome_uf", "id_regiao"),
        _linhas_estados(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_MESORREGIOES,
        ("id_mesorregiao", "nome_mesorregiao", "id_uf"),
        _linhas_mesorregioes(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_MICRORREGIOES,
        ("id_microrregiao", "nome_microrregiao", "id_mesorregiao"),
        _linhas_microrregioes(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_REGIOES_INTERMEDIARIAS,
        ("id_regiao_intermediaria", "nome_regiao_intermediaria", "id_uf"),
        _linhas_regioes_intermediarias(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_REGIOES_IMEDIATAS,
        ("id_regiao_imediata", "nome_regiao_imediata", "id_regiao_intermediaria"),
        _linhas_regioes_imediatas(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_MUNICIPIOS,
        ("id_municipio", "nome_municipio", "id_uf", "id_microrregiao", "id_regiao_imediata"),
        _linhas_municipios(data_dir),
    )
    return [
        ARQUIVO_DIM_REGIOES,
        ARQUIVO_DIM_ESTADOS,
        ARQUIVO_DIM_MESORREGIOES,
        ARQUIVO_DIM_MICRORREGIOES,
        ARQUIVO_DIM_REGIOES_INTERMEDIARIAS,
        ARQUIVO_DIM_REGIOES_IMEDIATAS,
        ARQUIVO_DIM_MUNICIPIOS,
    ]
