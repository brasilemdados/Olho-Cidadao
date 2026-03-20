"""Testes da geracao de grafos analiticos."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from infra.errors import UserInputError
from utils.grafo import GeradorGrafos


class GeracaoGrafoTestCase(unittest.TestCase):
    """Valida o contrato público da camada `data/grafo`."""

    def _escrever_csv(self, caminho: Path, cabecalho: list[str], *linhas: list[object]) -> None:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        conteudo = [",".join(cabecalho), *(",".join(map(str, linha)) for linha in linhas)]
        caminho.write_text("\n".join(conteudo) + "\n", encoding="utf-8")

    def _criar_csvs_minimos(self, base: Path) -> Path:
        csv_dir = base / "csv"
        self._escrever_csv(
            csv_dir / "dim_deputados_federais_referencia.csv",
            [
                "id_deputado",
                "nome_referencia",
                "sigla_uf_referencia",
                "primeira_legislatura",
                "ultima_legislatura",
            ],
            ["123", "Deputado Exemplo", "SP", "57", "57"],
        )
        self._escrever_csv(
            csv_dir / "dim_senadores.csv",
            ["id_senador", "nome_senador"],
            ["22", "Senador Exemplo"],
        )
        self._escrever_csv(
            csv_dir / "dim_fornecedores.csv",
            ["id_fornecedor", "documento", "tipo_documento", "cnpj_base", "nome_principal"],
            ["12345678000190", "12345678000190", "cnpj", "12345678", "Fornecedor Camara"],
            ["07425595000176", "07425595000176", "cnpj", "07425595", "Fornecedor Senado"],
        )
        self._escrever_csv(
            csv_dir / "dim_tipos_despesa.csv",
            ["id_tipo_despesa", "origem", "tipo_despesa"],
            ["camara:combustivel", "camara", "COMBUSTIVEL"],
            [
                "senado:aluguel_de_imoveis_para_escritorio_politico",
                "senado",
                "Aluguel de imóveis para escritório político",
            ],
        )
        self._escrever_csv(
            csv_dir / "tb_documentos_despesas_deputados.csv",
            [
                "id_documento_despesa",
                "id_fornecedor",
                "id_tipo_documento_fiscal",
                "id_tempo_documento",
                "numero_documento",
                "valor_documento",
            ],
            ["7514302", "12345678000190", "camara:0:nota_fiscal", "2025-04-10", "NF-29", "100.00"],
        )
        self._escrever_csv(
            csv_dir / "tb_despesas_deputados.csv",
            [
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
            ],
            [
                "desp-cam-1",
                "7514302",
                "123",
                "57",
                "camara:combustivel",
                "2025-03",
                "111",
                "",
                "0",
                "0.00",
                "100.00",
            ],
        )
        self._escrever_csv(
            csv_dir / "tb_documentos_despesas_senadores.csv",
            [
                "id_documento_despesa",
                "id_fornecedor",
                "id_tipo_documento_fiscal",
                "id_tempo_documento",
                "numero_documento",
                "detalhamento",
            ],
            ["doc-sen-1", "07425595000176", "senado::recibo", "2025-03-09", "112752", "Pagamento de internet"],
        )
        self._escrever_csv(
            csv_dir / "tb_despesas_senadores.csv",
            [
                "id_despesa_senador",
                "id_documento_despesa",
                "id_senador",
                "id_tipo_despesa",
                "id_competencia",
                "valor_reembolsado",
            ],
            [
                "1",
                "doc-sen-1",
                "22",
                "senado:aluguel_de_imoveis_para_escritorio_politico",
                "2025-02",
                "281.58",
            ],
        )
        return csv_dir

    def test_gerador_gera_jsons_compativeis_com_cytoscape(self):
        """O gerador deve publicar um JSON de rede e um resumo verificável."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_dir = self._criar_csvs_minimos(base)
            output_dir = base / "grafo"

            gerados = GeradorGrafos(csv_dir=csv_dir, output_dir=output_dir).executar()

            self.assertEqual(
                gerados,
                [
                    "rede_despesas_publicas.cytoscape.json",
                    "resumo_rede_despesas_publicas.json",
                ],
            )

            grafo = json.loads((output_dir / "rede_despesas_publicas.cytoscape.json").read_text(encoding="utf-8"))
            resumo = json.loads((output_dir / "resumo_rede_despesas_publicas.json").read_text(encoding="utf-8"))

            self.assertEqual(grafo["metadata"]["framework_recomendado"]["nome"], "cytoscape.js")
            self.assertEqual(resumo["contagens"]["nos_parlamentares"], 2)
            self.assertEqual(resumo["contagens"]["nos_fornecedores"], 2)
            self.assertEqual(resumo["contagens"]["nos_tipos_despesa"], 2)
            self.assertEqual(resumo["contagens"]["arestas_parlamentar_fornecedor"], 2)
            self.assertEqual(resumo["contagens"]["arestas_parlamentar_tipo"], 2)

            ids_nos = {item["data"]["id"] for item in grafo["elements"]["nodes"]}
            self.assertIn("dep:123", ids_nos)
            self.assertIn("sen:22", ids_nos)
            self.assertIn("forn:12345678000190", ids_nos)
            self.assertIn("tipo:camara:combustivel", ids_nos)

            relacoes = {item["data"]["id"]: item["data"] for item in grafo["elements"]["edges"]}
            self.assertIn("rel:fornecedor:dep:123:forn:12345678000190", relacoes)
            self.assertEqual(
                relacoes["rel:fornecedor:dep:123:forn:12345678000190"]["valor_total"],
                100.0,
            )

    def test_gerador_falha_quando_camada_csv_esta_incompleta(self):
        """A geração do grafo deve exigir o conjunto mínimo da camada CSV."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_dir = base / "csv"
            csv_dir.mkdir()

            with self.assertRaises(UserInputError) as ctx:
                GeradorGrafos(csv_dir=csv_dir, output_dir=base / "grafo").executar()

        self.assertIn("gerar-grafo", str(ctx.exception))
        self.assertIn("dim_fornecedores.csv", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
