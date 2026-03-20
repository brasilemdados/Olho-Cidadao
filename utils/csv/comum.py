"""Helpers enxutos para gerar a camada analitica em CSV."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


@dataclass(frozen=True)
class FonteObrigatoria:
    """Representa um artefato minimo exigido antes da geracao dos CSVs."""

    padrao: str
    descricao: str


def _valor_csv(valor: Any) -> Any:
    """Normaliza valores para escrita em CSV."""

    if valor is None:
        return ""
    if isinstance(valor, (dict, list)):
        return json.dumps(valor, ensure_ascii=False)
    return valor


def escrever_csv(
    destino: Path,
    colunas: Sequence[str],
    linhas: Iterable[Sequence[Any]],
) -> int:
    """Escreve um arquivo CSV simples e retorna a quantidade de linhas."""

    destino.parent.mkdir(parents=True, exist_ok=True)
    total = 0

    with destino.open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(list(colunas))
        for linha in linhas:
            writer.writerow([_valor_csv(valor) for valor in linha])
            total += 1

    return total


def iterar_registros_json(caminho: Path) -> Iterator[dict[str, Any]]:
    """Itera registros de um arquivo JSON objeto, lista ou JSON Lines."""

    conteudo = caminho.read_text(encoding="utf-8").strip()
    if not conteudo:
        return

    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError:
        for linha in conteudo.splitlines():
            linha = linha.strip()
            if not linha:
                continue
            try:
                registro = json.loads(linha)
            except json.JSONDecodeError:
                continue
            if isinstance(registro, dict):
                yield registro
        return

    if isinstance(dados, list):
        for item in dados:
            if isinstance(item, dict):
                yield item
        return

    if isinstance(dados, dict):
        yield dados


def iterar_registros_em_arquivos(caminhos: Iterable[Path]) -> Iterator[dict[str, Any]]:
    """Encadeia a leitura de varios arquivos JSON/JSONL."""

    for caminho in caminhos:
        yield from iterar_registros_json(caminho)


def ordenar_numero_texto(valor: Any) -> tuple[int, int | str]:
    """Ordena numeros como numeros e o restante como texto."""

    texto = str(valor or "")
    if texto.isdigit():
        return (0, int(texto))
    return (1, texto)


def hash_id(*partes: Any, tamanho: int = 16) -> str:
    """Cria um identificador estável e curto a partir de partes textuais."""

    bruto = "|".join("" if parte is None else str(parte) for parte in partes)
    return hashlib.sha1(bruto.encode("utf-8")).hexdigest()[:tamanho]


def slug_texto(valor: Any) -> str:
    """Gera um slug ASCII estável para uso em IDs analíticos."""

    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = texto.encode("ascii", "ignore").decode("ascii").lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    return texto or "nao_informado"


def normalizar_data_iso(valor: Any) -> str:
    """Converte datas ISO comuns para `YYYY-MM-DD`."""

    if valor in (None, ""):
        return ""

    texto = str(valor).strip()
    if not texto:
        return ""

    for candidato in (texto, texto.replace("Z", "+00:00")):
        try:
            return datetime.fromisoformat(candidato).date().isoformat()
        except ValueError:
            continue

    if len(texto) >= 10:
        prefixo = texto[:10]
        try:
            return date.fromisoformat(prefixo).isoformat()
        except ValueError:
            return ""
    return ""


def id_tempo(valor: Any) -> str:
    """Deriva a chave natural de uma data na dimensão tempo."""

    return normalizar_data_iso(valor)


def id_competencia(ano: Any, mes: Any) -> str:
    """Deriva a chave natural da competência mensal."""

    try:
        ano_int = int(ano)
        mes_int = int(mes)
    except (TypeError, ValueError):
        return ""

    if mes_int < 1 or mes_int > 12:
        return ""
    return f"{ano_int:04d}-{mes_int:02d}"


def id_tipo_documento_fiscal(
    origem: str,
    codigo: Any,
    nome: Any,
) -> str:
    """Gera a chave da dimensão de tipos de documento fiscal."""

    codigo_texto = "" if codigo in (None, "") else str(codigo)
    return f"{origem}:{codigo_texto}:{slug_texto(nome)}"


def id_tipo_despesa(origem: str, nome: Any) -> str:
    """Gera a chave da dimensão de tipos de despesa."""

    return f"{origem}:{slug_texto(nome)}"
