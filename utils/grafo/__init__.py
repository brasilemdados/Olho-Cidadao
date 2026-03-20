"""Fachada publica e orquestracao unica da geracao de grafos analiticos."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from configuracao.logger import logger
from infra.errors import UserInputError


ARQUIVO_GRAFO = "rede_despesas_publicas.cytoscape.json"
ARQUIVO_RESUMO = "resumo_rede_despesas_publicas.json"
ARQUIVOS_OBRIGATORIOS = (
    "dim_deputados_federais_referencia.csv",
    "dim_senadores.csv",
    "dim_fornecedores.csv",
    "dim_tipos_despesa.csv",
    "tb_documentos_despesas_deputados.csv",
    "tb_despesas_deputados.csv",
    "tb_documentos_despesas_senadores.csv",
    "tb_despesas_senadores.csv",
)


@dataclass(frozen=True)
class FonteObrigatoriaGrafo:
    """Representa um arquivo mínimo exigido para montar a rede analítica."""

    nome: str


FONTES_OBRIGATORIAS: tuple[FonteObrigatoriaGrafo, ...] = tuple(
    FonteObrigatoriaGrafo(nome=nome) for nome in ARQUIVOS_OBRIGATORIOS
)


def _ler_csv_por_id(caminho: Path, chave: str) -> dict[str, dict[str, str]]:
    with caminho.open(encoding="utf-8") as arquivo:
        return {linha[chave]: linha for linha in csv.DictReader(arquivo)}


def _como_float(valor: str | None) -> float:
    if valor in (None, ""):
        return 0.0
    try:
        return float(valor)
    except ValueError:
        return 0.0


def _arredondar(valor: float) -> float:
    return round(valor, 2)


def _atualizar_intervalo_competencia(agregado: dict[str, Any], competencia: str) -> None:
    if not competencia:
        return
    primeira = agregado.get("primeira_competencia") or ""
    ultima = agregado.get("ultima_competencia") or ""
    if not primeira or competencia < primeira:
        agregado["primeira_competencia"] = competencia
    if not ultima or competencia > ultima:
        agregado["ultima_competencia"] = competencia


def _top_lista(itens: list[dict[str, Any]], chave, limite: int = 20) -> list[dict[str, Any]]:
    return sorted(itens, key=chave, reverse=True)[:limite]


class GeradorGrafos:
    """Gera grafos analíticos a partir da camada normalizada em CSV."""

    def __init__(
        self,
        csv_dir: str | Path = "data/csv",
        output_dir: str | Path = "data/grafo",
    ) -> None:
        self.csv_dir = Path(csv_dir)
        self.output_dir = Path(output_dir)

    def validar_fontes(self) -> None:
        """Falha cedo quando a camada CSV ainda nao esta pronta."""

        faltando = [
            str(self.csv_dir / fonte.nome)
            for fonte in FONTES_OBRIGATORIAS
            if not (self.csv_dir / fonte.nome).exists()
        ]
        if faltando:
            detalhes = "\n".join(f"- {item}" for item in faltando)
            raise UserInputError(
                "O comando `gerar-grafo` depende da camada CSV analitica pronta. "
                "Arquivos ausentes:\n"
                f"{detalhes}"
            )

    def _agregar_rede(self) -> tuple[dict[str, Any], dict[str, Any]]:
        dep_ref = _ler_csv_por_id(
            self.csv_dir / "dim_deputados_federais_referencia.csv",
            "id_deputado",
        )
        senadores = _ler_csv_por_id(self.csv_dir / "dim_senadores.csv", "id_senador")
        fornecedores = _ler_csv_por_id(self.csv_dir / "dim_fornecedores.csv", "id_fornecedor")
        tipos_despesa = _ler_csv_por_id(self.csv_dir / "dim_tipos_despesa.csv", "id_tipo_despesa")
        docs_camara = _ler_csv_por_id(
            self.csv_dir / "tb_documentos_despesas_deputados.csv",
            "id_documento_despesa",
        )
        docs_senado = _ler_csv_por_id(
            self.csv_dir / "tb_documentos_despesas_senadores.csv",
            "id_documento_despesa",
        )

        ator_fornecedor: dict[tuple[str, str], dict[str, Any]] = {}
        ator_tipo: dict[tuple[str, str], dict[str, Any]] = {}
        metricas_atores: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"valor_total": 0.0, "quantidade_despesas": 0}
        )
        metricas_fornecedores: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"valor_total": 0.0, "quantidade_despesas": 0}
        )
        metricas_tipos: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"valor_total": 0.0, "quantidade_despesas": 0}
        )
        contagem_casas = {"camara": 0, "senado": 0}

        with (self.csv_dir / "tb_despesas_deputados.csv").open(encoding="utf-8") as arquivo:
            for linha in csv.DictReader(arquivo):
                documento = docs_camara.get(linha["id_documento_despesa"]) or {}
                fornecedor_id = documento.get("id_fornecedor") or ""
                if not fornecedor_id:
                    continue

                ator_id = f"dep:{linha['id_deputado']}"
                tipo_id = f"tipo:{linha['id_tipo_despesa']}"
                fornecedor_no = f"forn:{fornecedor_id}"
                valor = _como_float(linha.get("valor_liquido"))
                competencia = linha.get("id_competencia") or ""
                contagem_casas["camara"] += 1

                agregado_fornecedor = ator_fornecedor.setdefault(
                    (ator_id, fornecedor_no),
                    {
                        "casa": "camara",
                        "quantidade_despesas": 0,
                        "valor_total": 0.0,
                        "primeira_competencia": "",
                        "ultima_competencia": "",
                        "tipos_despesa": set(),
                    },
                )
                agregado_fornecedor["quantidade_despesas"] += 1
                agregado_fornecedor["valor_total"] += valor
                agregado_fornecedor["tipos_despesa"].add(tipo_id)
                _atualizar_intervalo_competencia(agregado_fornecedor, competencia)

                agregado_tipo = ator_tipo.setdefault(
                    (ator_id, tipo_id),
                    {
                        "casa": "camara",
                        "quantidade_despesas": 0,
                        "valor_total": 0.0,
                        "primeira_competencia": "",
                        "ultima_competencia": "",
                        "fornecedores": set(),
                    },
                )
                agregado_tipo["quantidade_despesas"] += 1
                agregado_tipo["valor_total"] += valor
                agregado_tipo["fornecedores"].add(fornecedor_no)
                _atualizar_intervalo_competencia(agregado_tipo, competencia)

                metricas_atores[ator_id]["valor_total"] += valor
                metricas_atores[ator_id]["quantidade_despesas"] += 1
                metricas_fornecedores[fornecedor_no]["valor_total"] += valor
                metricas_fornecedores[fornecedor_no]["quantidade_despesas"] += 1
                metricas_tipos[tipo_id]["valor_total"] += valor
                metricas_tipos[tipo_id]["quantidade_despesas"] += 1

        with (self.csv_dir / "tb_despesas_senadores.csv").open(encoding="utf-8") as arquivo:
            for linha in csv.DictReader(arquivo):
                documento = docs_senado.get(linha["id_documento_despesa"]) or {}
                fornecedor_id = documento.get("id_fornecedor") or ""
                if not fornecedor_id:
                    continue

                ator_id = f"sen:{linha['id_senador']}"
                tipo_id = f"tipo:{linha['id_tipo_despesa']}"
                fornecedor_no = f"forn:{fornecedor_id}"
                valor = _como_float(linha.get("valor_reembolsado"))
                competencia = linha.get("id_competencia") or ""
                contagem_casas["senado"] += 1

                agregado_fornecedor = ator_fornecedor.setdefault(
                    (ator_id, fornecedor_no),
                    {
                        "casa": "senado",
                        "quantidade_despesas": 0,
                        "valor_total": 0.0,
                        "primeira_competencia": "",
                        "ultima_competencia": "",
                        "tipos_despesa": set(),
                    },
                )
                agregado_fornecedor["quantidade_despesas"] += 1
                agregado_fornecedor["valor_total"] += valor
                agregado_fornecedor["tipos_despesa"].add(tipo_id)
                _atualizar_intervalo_competencia(agregado_fornecedor, competencia)

                agregado_tipo = ator_tipo.setdefault(
                    (ator_id, tipo_id),
                    {
                        "casa": "senado",
                        "quantidade_despesas": 0,
                        "valor_total": 0.0,
                        "primeira_competencia": "",
                        "ultima_competencia": "",
                        "fornecedores": set(),
                    },
                )
                agregado_tipo["quantidade_despesas"] += 1
                agregado_tipo["valor_total"] += valor
                agregado_tipo["fornecedores"].add(fornecedor_no)
                _atualizar_intervalo_competencia(agregado_tipo, competencia)

                metricas_atores[ator_id]["valor_total"] += valor
                metricas_atores[ator_id]["quantidade_despesas"] += 1
                metricas_fornecedores[fornecedor_no]["valor_total"] += valor
                metricas_fornecedores[fornecedor_no]["quantidade_despesas"] += 1
                metricas_tipos[tipo_id]["valor_total"] += valor
                metricas_tipos[tipo_id]["quantidade_despesas"] += 1

        grau_ator_fornecedores: dict[str, int] = defaultdict(int)
        grau_fornecedor_atores: dict[str, int] = defaultdict(int)
        grau_ator_tipos: dict[str, int] = defaultdict(int)
        grau_tipo_atores: dict[str, int] = defaultdict(int)

        for ator_id, fornecedor_id in ator_fornecedor:
            grau_ator_fornecedores[ator_id] += 1
            grau_fornecedor_atores[fornecedor_id] += 1

        for ator_id, tipo_id in ator_tipo:
            grau_ator_tipos[ator_id] += 1
            grau_tipo_atores[tipo_id] += 1

        atores_utilizados = {ator_id for ator_id, _ in ator_fornecedor} | {
            ator_id for ator_id, _ in ator_tipo
        }
        fornecedores_utilizados = {fornecedor_id for _, fornecedor_id in ator_fornecedor}
        tipos_utilizados = {tipo_id for _, tipo_id in ator_tipo}

        nodes: list[dict[str, Any]] = []
        for ator_id in sorted(atores_utilizados):
            casa, codigo = ator_id.split(":", maxsplit=1)
            if casa == "dep":
                base = dep_ref.get(codigo, {})
                data = {
                    "id": ator_id,
                    "label": base.get("nome_referencia") or codigo,
                    "tipo_no": "parlamentar",
                    "casa": "camara",
                    "id_origem": codigo,
                    "sigla_uf": base.get("sigla_uf_referencia") or "",
                    "primeira_legislatura": base.get("primeira_legislatura") or "",
                    "ultima_legislatura": base.get("ultima_legislatura") or "",
                    "quantidade_despesas": int(metricas_atores[ator_id]["quantidade_despesas"]),
                    "valor_total": _arredondar(float(metricas_atores[ator_id]["valor_total"])),
                    "grau_fornecedores": grau_ator_fornecedores.get(ator_id, 0),
                    "grau_tipos_despesa": grau_ator_tipos.get(ator_id, 0),
                }
                classes = "no parlamentar camara"
            else:
                base = senadores.get(codigo, {})
                data = {
                    "id": ator_id,
                    "label": base.get("nome_senador") or codigo,
                    "tipo_no": "parlamentar",
                    "casa": "senado",
                    "id_origem": codigo,
                    "quantidade_despesas": int(metricas_atores[ator_id]["quantidade_despesas"]),
                    "valor_total": _arredondar(float(metricas_atores[ator_id]["valor_total"])),
                    "grau_fornecedores": grau_ator_fornecedores.get(ator_id, 0),
                    "grau_tipos_despesa": grau_ator_tipos.get(ator_id, 0),
                }
                classes = "no parlamentar senado"
            nodes.append({"data": data, "classes": classes})

        for fornecedor_no in sorted(fornecedores_utilizados):
            codigo = fornecedor_no.split(":", maxsplit=1)[1]
            base = fornecedores.get(codigo, {})
            nodes.append(
                {
                    "data": {
                        "id": fornecedor_no,
                        "label": base.get("nome_principal") or codigo,
                        "tipo_no": "fornecedor",
                        "id_origem": codigo,
                        "documento": base.get("documento") or codigo,
                        "tipo_documento": base.get("tipo_documento") or "",
                        "cnpj_base": base.get("cnpj_base") or "",
                        "quantidade_despesas": int(
                            metricas_fornecedores[fornecedor_no]["quantidade_despesas"]
                        ),
                        "valor_total": _arredondar(
                            float(metricas_fornecedores[fornecedor_no]["valor_total"])
                        ),
                        "grau_parlamentares": grau_fornecedor_atores.get(fornecedor_no, 0),
                    },
                    "classes": "no fornecedor",
                }
            )

        for tipo_no in sorted(tipos_utilizados):
            codigo = tipo_no.split(":", maxsplit=1)[1]
            base = tipos_despesa.get(codigo, {})
            nodes.append(
                {
                    "data": {
                        "id": tipo_no,
                        "label": base.get("tipo_despesa") or codigo,
                        "tipo_no": "tipo_despesa",
                        "id_origem": codigo,
                        "origem": base.get("origem") or "",
                        "quantidade_despesas": int(metricas_tipos[tipo_no]["quantidade_despesas"]),
                        "valor_total": _arredondar(float(metricas_tipos[tipo_no]["valor_total"])),
                        "grau_parlamentares": grau_tipo_atores.get(tipo_no, 0),
                    },
                    "classes": f"no tipo_despesa {base.get('origem') or 'desconhecido'}",
                }
            )

        edges: list[dict[str, Any]] = []
        for (ator_id, fornecedor_no), agregado in sorted(ator_fornecedor.items()):
            edges.append(
                {
                    "data": {
                        "id": f"rel:fornecedor:{ator_id}:{fornecedor_no}",
                        "source": ator_id,
                        "target": fornecedor_no,
                        "tipo_relacao": "gasto_com_fornecedor",
                        "casa": agregado["casa"],
                        "quantidade_despesas": agregado["quantidade_despesas"],
                        "valor_total": _arredondar(agregado["valor_total"]),
                        "primeira_competencia": agregado["primeira_competencia"],
                        "ultima_competencia": agregado["ultima_competencia"],
                        "tipos_despesa_distintos": len(agregado["tipos_despesa"]),
                    },
                    "classes": f"relacao gasto_com_fornecedor {agregado['casa']}",
                }
            )

        for (ator_id, tipo_no), agregado in sorted(ator_tipo.items()):
            edges.append(
                {
                    "data": {
                        "id": f"rel:tipo:{ator_id}:{tipo_no}",
                        "source": ator_id,
                        "target": tipo_no,
                        "tipo_relacao": "gastou_em_tipo_despesa",
                        "casa": agregado["casa"],
                        "quantidade_despesas": agregado["quantidade_despesas"],
                        "valor_total": _arredondar(agregado["valor_total"]),
                        "primeira_competencia": agregado["primeira_competencia"],
                        "ultima_competencia": agregado["ultima_competencia"],
                        "fornecedores_distintos": len(agregado["fornecedores"]),
                    },
                    "classes": f"relacao gastou_em_tipo_despesa {agregado['casa']}",
                }
            )

        nodes_by_id = {item["data"]["id"]: item["data"] for item in nodes}

        top_fornecedores = _top_lista(
            [item["data"] for item in nodes if item["data"]["tipo_no"] == "fornecedor"],
            chave=lambda item: (item["valor_total"], item["quantidade_despesas"]),
        )
        top_parlamentares = _top_lista(
            [item["data"] for item in nodes if item["data"]["tipo_no"] == "parlamentar"],
            chave=lambda item: (item["valor_total"], item["quantidade_despesas"]),
        )
        top_relacoes_valor = _top_lista(
            [item["data"] for item in edges if item["data"]["tipo_relacao"] == "gasto_com_fornecedor"],
            chave=lambda item: (item["valor_total"], item["quantidade_despesas"]),
        )
        top_relacoes_qtd = _top_lista(
            [item["data"] for item in edges if item["data"]["tipo_relacao"] == "gasto_com_fornecedor"],
            chave=lambda item: (item["quantidade_despesas"], item["valor_total"]),
        )

        resumo = {
            "nome": "rede_despesas_publicas",
            "framework_recomendado": "cytoscape.js",
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
            "contagens": {
                "nos": len(nodes),
                "arestas": len(edges),
                "nos_parlamentares": sum(
                    1 for item in nodes if item["data"]["tipo_no"] == "parlamentar"
                ),
                "nos_fornecedores": sum(
                    1 for item in nodes if item["data"]["tipo_no"] == "fornecedor"
                ),
                "nos_tipos_despesa": sum(
                    1 for item in nodes if item["data"]["tipo_no"] == "tipo_despesa"
                ),
                "arestas_parlamentar_fornecedor": sum(
                    1
                    for item in edges
                    if item["data"]["tipo_relacao"] == "gasto_com_fornecedor"
                ),
                "arestas_parlamentar_tipo": sum(
                    1
                    for item in edges
                    if item["data"]["tipo_relacao"] == "gastou_em_tipo_despesa"
                ),
                "despesas_processadas_camara": contagem_casas["camara"],
                "despesas_processadas_senado": contagem_casas["senado"],
            },
            "top_fornecedores_por_valor": [
                {
                    "id": item["id"],
                    "label": item["label"],
                    "valor_total": item["valor_total"],
                    "quantidade_despesas": item["quantidade_despesas"],
                    "grau_parlamentares": item["grau_parlamentares"],
                }
                for item in top_fornecedores
            ],
            "top_parlamentares_por_valor": [
                {
                    "id": item["id"],
                    "label": item["label"],
                    "casa": item["casa"],
                    "valor_total": item["valor_total"],
                    "quantidade_despesas": item["quantidade_despesas"],
                    "grau_fornecedores": item["grau_fornecedores"],
                }
                for item in top_parlamentares
            ],
            "top_relacoes_parlamentar_fornecedor_por_valor": [
                {
                    "source": item["source"],
                    "source_label": nodes_by_id[item["source"]]["label"],
                    "target": item["target"],
                    "target_label": nodes_by_id[item["target"]]["label"],
                    "casa": item["casa"],
                    "valor_total": item["valor_total"],
                    "quantidade_despesas": item["quantidade_despesas"],
                    "primeira_competencia": item["primeira_competencia"],
                    "ultima_competencia": item["ultima_competencia"],
                }
                for item in top_relacoes_valor
            ],
            "top_relacoes_parlamentar_fornecedor_por_quantidade": [
                {
                    "source": item["source"],
                    "source_label": nodes_by_id[item["source"]]["label"],
                    "target": item["target"],
                    "target_label": nodes_by_id[item["target"]]["label"],
                    "casa": item["casa"],
                    "valor_total": item["valor_total"],
                    "quantidade_despesas": item["quantidade_despesas"],
                    "primeira_competencia": item["primeira_competencia"],
                    "ultima_competencia": item["ultima_competencia"],
                }
                for item in top_relacoes_qtd
            ],
        }

        grafo = {
            "metadata": {
                "nome": "rede_despesas_publicas",
                "descricao": (
                    "Rede agregada de parlamentares, fornecedores e tipos de despesa "
                    "derivada de data/csv."
                ),
                "formato": "cytoscape.js/elements",
                "framework_recomendado": {
                    "nome": "cytoscape.js",
                    "wrapper_react": "react-cytoscapejs",
                    "licenca": "MIT",
                },
                "gerado_em": datetime.now().isoformat(timespec="seconds"),
                "fontes": [str(self.csv_dir / item) for item in ARQUIVOS_OBRIGATORIOS],
                "contagens": resumo["contagens"],
                "verificacao": {
                    "gasto_com_fornecedor": {
                        "camara": (
                            "JOIN tb_despesas_deputados.csv -> "
                            "tb_documentos_despesas_deputados.csv por "
                            "id_documento_despesa; GROUP BY id_deputado, id_fornecedor"
                        ),
                        "senado": (
                            "JOIN tb_despesas_senadores.csv -> "
                            "tb_documentos_despesas_senadores.csv por "
                            "id_documento_despesa; GROUP BY id_senador, id_fornecedor"
                        ),
                    },
                    "gastou_em_tipo_despesa": (
                        "GROUP BY parlamentar, id_tipo_despesa sobre os fatos "
                        "de despesas das duas casas"
                    ),
                },
            },
            "elements": {"nodes": nodes, "edges": edges},
        }
        return grafo, resumo

    def executar(self) -> list[str]:
        """Gera os artefatos de rede derivados da camada CSV."""

        self.validar_fontes()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=== INICIANDO GERACAO DE GRAFO ANALITICO ===")
        grafo, resumo = self._agregar_rede()

        with (self.output_dir / ARQUIVO_GRAFO).open("w", encoding="utf-8") as arquivo:
            json.dump(grafo, arquivo, ensure_ascii=False, separators=(",", ":"))

        with (self.output_dir / ARQUIVO_RESUMO).open("w", encoding="utf-8") as arquivo:
            json.dump(resumo, arquivo, ensure_ascii=False, indent=2)

        logger.info(
            "=== GERACAO DE GRAFO ANALITICO FINALIZADA | nos=%s | arestas=%s ===",
            resumo["contagens"]["nos"],
            resumo["contagens"]["arestas"],
        )
        return [ARQUIVO_GRAFO, ARQUIVO_RESUMO]


def executar_geracao_grafo(
    csv_dir: str | Path = "data/csv",
    output_dir: str | Path = "data/grafo",
) -> list[str]:
    """Atalho funcional para a geracao completa do grafo analitico."""

    return GeradorGrafos(csv_dir=csv_dir, output_dir=output_dir).executar()


__all__ = ["GeradorGrafos", "FONTES_OBRIGATORIAS", "executar_geracao_grafo"]
