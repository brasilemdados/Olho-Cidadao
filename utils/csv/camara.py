"""Geracao da camada analitica da Camara dos Deputados."""

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
from .comum import iterar_registros_json
from .comum import ordenar_numero_texto

ARQUIVO_DIM_DEPUTADOS = "dim_dep_federal.csv"
ARQUIVO_DIM_DEPUTADOS_REFERENCIA = "dim_deputados_federais_referencia.csv"
ARQUIVO_DIM_LEGISLATURAS = "dim_legislaturas_dep_federais.csv"
ARQUIVO_TB_DOCUMENTOS = "tb_documentos_despesas_deputados.csv"
ARQUIVO_TB_DESPESAS = "tb_despesas_deputados.csv"

FONTES_OBRIGATORIAS = (
    FonteObrigatoria("legislaturas.json", "lista de legislaturas da Camara"),
    FonteObrigatoria(
        "deputados_por_legislaturas/*.json",
        "deputados por legislatura da Camara",
    ),
    FonteObrigatoria(
        "despesas_deputados_federais/**/*.json",
        "despesas dos deputados federais",
    ),
)


def _caminhos_deputados(data_dir: Path) -> list[Path]:
    return sorted((data_dir / "deputados_por_legislaturas").glob("*.json"))


def _caminhos_despesas(data_dir: Path) -> list[Path]:
    return sorted((data_dir / "despesas_deputados_federais").glob("**/*.json"))


def iterar_registros_despesa_camara(data_dir: Path):
    """Itera as despesas da Camara com chaves analiticas derivadas."""

    for registro in iterar_registros_em_arquivos(_caminhos_despesas(data_dir)):
        id_documento = registro.get("id_documento_despesa") or registro.get("codDocumento")
        if not id_documento:
            id_documento = hash_id(
                "documento_camara",
                registro.get("cnpjCpfFornecedor"),
                registro.get("numDocumento"),
                registro.get("dataDocumento"),
                registro.get("valorDocumento"),
            )

        yield {
            **registro,
            "id_documento_despesa": str(id_documento),
            "id_tempo_documento": id_tempo(
                registro.get("data_documento") or registro.get("dataDocumento")
            ),
            "id_competencia": id_competencia(registro.get("ano"), registro.get("mes")),
            "id_tipo_despesa": id_tipo_despesa("camara", registro.get("tipoDespesa")),
            "id_tipo_documento_fiscal": id_tipo_documento_fiscal(
                "camara",
                registro.get("codTipoDocumento"),
                registro.get("tipoDocumento"),
            ),
            "id_despesa_deputado": hash_id(
                "despesa_camara",
                registro.get("id_deputado"),
                id_documento,
                registro.get("ano"),
                registro.get("mes"),
                registro.get("parcela"),
                registro.get("numRessarcimento"),
                registro.get("valorLiquido"),
                registro.get("valorGlosa"),
            ),
        }


def _linhas_legislaturas(data_dir: Path) -> list[list[object]]:
    linhas = []
    for registro in iterar_registros_json(data_dir / "legislaturas.json"):
        linhas.append(
            [
                registro.get("id"),
                registro.get("dataInicio"),
                registro.get("dataFim"),
            ]
        )
    return linhas


def _linhas_deputados(data_dir: Path) -> list[list[object]]:
    registros_unicos: dict[tuple[object, object], list[object]] = {}

    for registro in iterar_registros_em_arquivos(_caminhos_deputados(data_dir)):
        chave = (
            registro.get("id"),
            registro.get("idLegislatura") or registro.get("id_legislatura"),
        )
        if chave in registros_unicos:
            continue
        registros_unicos[chave] = [
            registro.get("id"),
            registro.get("nome"),
            registro.get("siglaPartido"),
            registro.get("siglaUf"),
            registro.get("idLegislatura") or registro.get("id_legislatura"),
        ]

    return [
        registros_unicos[chave]
        for chave in sorted(
            registros_unicos,
            key=lambda item: (
                ordenar_numero_texto(item[1]),
                ordenar_numero_texto(item[0]),
            ),
        )
    ]


def _linhas_deputados_referencia(data_dir: Path) -> list[list[object]]:
    agregados: dict[object, dict[str, object]] = {}

    for registro in iterar_registros_em_arquivos(_caminhos_deputados(data_dir)):
        id_deputado = registro.get("id")
        id_legislatura = registro.get("idLegislatura") or registro.get("id_legislatura")
        if id_deputado is None or id_legislatura is None:
            continue

        atual = agregados.setdefault(
            id_deputado,
            {
                "id_deputado": id_deputado,
                "nome_referencia": registro.get("nome"),
                "sigla_uf_referencia": registro.get("siglaUf"),
                "primeira_legislatura": id_legislatura,
                "ultima_legislatura": id_legislatura,
            },
        )
        if id_legislatura < atual["primeira_legislatura"]:
            atual["primeira_legislatura"] = id_legislatura
        if id_legislatura >= atual["ultima_legislatura"]:
            atual["ultima_legislatura"] = id_legislatura
            atual["nome_referencia"] = registro.get("nome")
            atual["sigla_uf_referencia"] = registro.get("siglaUf")

    return [
        [
            item["id_deputado"],
            item["nome_referencia"],
            item["sigla_uf_referencia"],
            item["primeira_legislatura"],
            item["ultima_legislatura"],
        ]
        for _, item in sorted(agregados.items(), key=lambda entrada: ordenar_numero_texto(entrada[0]))
    ]


def _linhas_documentos(data_dir: Path) -> list[list[object]]:
    documentos: dict[str, list[object]] = {}

    for registro in iterar_registros_despesa_camara(data_dir):
        chave = registro["id_documento_despesa"]
        if chave in documentos:
            continue
        documentos[chave] = [
            chave,
            registro.get("documento_fornecedor_normalizado"),
            registro.get("id_tipo_documento_fiscal"),
            registro.get("id_tempo_documento"),
            registro.get("numDocumento"),
            registro.get("valorDocumento"),
        ]

    return [documentos[chave] for chave in sorted(documentos, key=ordenar_numero_texto)]


def _linhas_despesas(data_dir: Path) -> list[list[object]]:
    linhas = []

    for registro in iterar_registros_despesa_camara(data_dir):
        linhas.append(
            [
                registro.get("id_despesa_deputado"),
                registro.get("id_documento_despesa"),
                registro.get("id_deputado"),
                registro.get("id_legislatura"),
                registro.get("id_tipo_despesa"),
                registro.get("id_competencia"),
                registro.get("codLote"),
                registro.get("numRessarcimento"),
                registro.get("parcela"),
                registro.get("valorGlosa"),
                registro.get("valorLiquido"),
            ]
        )

    return linhas


def gerar_csvs_camara(data_dir: Path, output_dir: Path) -> list[str]:
    """Gera os CSVs finais da Camara em formato analitico normalizado."""

    escrever_csv(
        output_dir / ARQUIVO_DIM_LEGISLATURAS,
        ("id_legislatura", "data_inicio", "data_fim"),
        _linhas_legislaturas(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_DEPUTADOS,
        (
            "id_deputado",
            "nome_deputado",
            "sigla_partido",
            "sigla_uf",
            "id_legislatura",
        ),
        _linhas_deputados(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_DIM_DEPUTADOS_REFERENCIA,
        (
            "id_deputado",
            "nome_referencia",
            "sigla_uf_referencia",
            "primeira_legislatura",
            "ultima_legislatura",
        ),
        _linhas_deputados_referencia(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_TB_DOCUMENTOS,
        (
            "id_documento_despesa",
            "id_fornecedor",
            "id_tipo_documento_fiscal",
            "id_tempo_documento",
            "numero_documento",
            "valor_documento",
        ),
        _linhas_documentos(data_dir),
    )
    escrever_csv(
        output_dir / ARQUIVO_TB_DESPESAS,
        (
            "id_despesa_deputado",
            "id_documento_despesa",
            "id_deputado",
            "id_legislatura",
            "id_tipo_despesa",
            "id_competencia",
            "lote_documentos",
            "numero_ressarcimento",
            "parcela",
            "valor_glosa",
            "valor_liquido",
        ),
        _linhas_despesas(data_dir),
    )
    return [
        ARQUIVO_DIM_LEGISLATURAS,
        ARQUIVO_DIM_DEPUTADOS,
        ARQUIVO_DIM_DEPUTADOS_REFERENCIA,
        ARQUIVO_TB_DOCUMENTOS,
        ARQUIVO_TB_DESPESAS,
    ]
