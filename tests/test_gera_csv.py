"""Testes da camada analitica final em CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from infra.errors import UserInputError
from utils.csv import GeradorCSVs


class GeracaoCSVTestCase(unittest.TestCase):
    """Valida o contrato da geração analítica em `data/csv`."""

    def _escrever_jsonl(self, caminho: Path, *registros: dict) -> None:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with caminho.open("w", encoding="utf-8") as arquivo:
            for registro in registros:
                json.dump(registro, arquivo, ensure_ascii=False)
                arquivo.write("\n")

    def _ler_csv(self, caminho: Path) -> list[list[str]]:
        with caminho.open(encoding="utf-8") as arquivo:
            return list(csv.reader(arquivo))

    def _criar_fontes_minimas(self, base: Path) -> Path:
        data_dir = base / "data"

        self._escrever_jsonl(
            data_dir / "legislaturas.json",
            {"id": 57, "dataInicio": "2023-02-01", "dataFim": "2027-01-31"},
        )
        self._escrever_jsonl(
            data_dir / "deputados_por_legislaturas" / "deputados_legislaturas_57.json",
            {
                "id": 123,
                "nome": "Deputado Exemplo",
                "siglaPartido": "ABC",
                "siglaUf": "SP",
                "idLegislatura": 57,
            },
        )
        self._escrever_jsonl(
            data_dir / "despesas_deputados_federais" / "2025" / "despesas_123.json",
            {
                "id_deputado": 123,
                "id_legislatura": 57,
                "nome_deputado": "Deputado Exemplo",
                "sigla_uf_deputado": "SP",
                "sigla_partido_deputado": "ABC",
                "nomeFornecedor": "Fornecedor Camara",
                "cnpjCpfFornecedor": "12345678000190",
                "documento_fornecedor_normalizado": "12345678000190",
                "tipo_documento_fornecedor": "cnpj",
                "cnpj_base_fornecedor": "12345678",
                "codDocumento": "7514302",
                "tipoDocumento": "Nota Fiscal",
                "codTipoDocumento": 0,
                "dataDocumento": "2025-04-10T00:00:00",
                "data_documento": "2025-04-10",
                "numDocumento": "NF-29",
                "codLote": 111,
                "numRessarcimento": "",
                "parcela": 0,
                "valorDocumento": "100.00",
                "valorGlosa": "0.00",
                "valorLiquido": "100.00",
                "ano": 2025,
                "mes": 3,
                "tipoDespesa": "COMBUSTIVEL",
            },
        )

        self._escrever_jsonl(
            data_dir / "ibge" / "localidades" / "regioes.json",
            {"payload": {"id": 1, "sigla": "N", "nome": "Norte"}},
        )
        self._escrever_jsonl(
            data_dir / "ibge" / "localidades" / "estados.json",
            {
                "payload": {
                    "id": 11,
                    "sigla": "RO",
                    "nome": "Rondonia",
                    "regiao": {"id": 1, "sigla": "N", "nome": "Norte"},
                }
            },
        )
        self._escrever_jsonl(
            data_dir / "ibge" / "localidades" / "municipios.json",
            {
                "payload": {
                    "id": 1100015,
                    "nome": "Alta Floresta D'Oeste",
                    "microrregiao": {
                        "id": 11006,
                        "nome": "Cacoal",
                        "mesorregiao": {
                            "id": 1102,
                            "nome": "Leste Rondoniense",
                            "UF": {
                                "id": 11,
                                "sigla": "RO",
                                "nome": "Rondonia",
                                "regiao": {"id": 1, "sigla": "N", "nome": "Norte"},
                            },
                        },
                    },
                    "regiao-imediata": {
                        "id": 110005,
                        "nome": "Cacoal",
                        "regiao-intermediaria": {
                            "id": 1102,
                            "nome": "Ji-Parana",
                            "UF": {
                                "id": 11,
                                "sigla": "RO",
                                "nome": "Rondonia",
                            },
                        },
                    },
                }
            },
        )

        self._escrever_jsonl(
            data_dir / "senadores" / "ceaps_2025.json",
            {
                "id": 1,
                "id_despesa_senado": 1,
                "codSenador": 22,
                "nomeSenador": "Senador Exemplo",
                "tipoDocumento": "Recibo",
                "fornecedor": "Fornecedor Senado",
                "cpfCnpj": "07425595000176",
                "documento_fornecedor_normalizado": "07425595000176",
                "tipo_documento_fornecedor": "cnpj",
                "cnpj_base_fornecedor": "07425595",
                "documento": "112752",
                "data": "2025-03-09",
                "data_documento": "2025-03-09",
                "detalhamento": "Pagamento de internet.",
                "tipoDespesa": "Aluguel de imóveis para escritório político",
                "valorReembolsado": 281.58,
                "ano": 2025,
                "mes": 2,
                "ano_arquivo": 2025,
                "orgao_origem": "senado",
                "endpoint_origem": "ceaps",
            },
        )

        self._escrever_jsonl(
            data_dir / "siconfi" / "entes" / "consulta=all.json",
            {
                "payload": {
                    "cod_ibge": 3527207,
                    "ente": "Lorena",
                    "capital": "0",
                    "regiao": "SE",
                    "uf": "SP",
                    "esfera": "M",
                    "exercicio": 2026,
                    "populacao": 87468,
                    "cnpj": "47563739000175",
                }
            },
        )

        self._escrever_jsonl(
            data_dir / "orcamento_item_despesa" / "orcamento_item_despesa_2024.json",
            {
                "ano": 2024,
                "id_item_despesa": "1177",
                "codigo_funcao": "01",
                "funcao": "Legislativa",
                "codigo_subfuncao": "031",
                "subfuncao": "Acao Legislativa",
                "codigo_programa": "0034",
                "programa": "Gestao Legislativa",
                "codigo_acao": "4061",
                "acao": "Processo Legislativo",
                "codigo_unidade_orcamentaria": "01101",
                "unidade_orcamentaria": "Camara dos Deputados",
                "codigo_fonte": "1000",
                "fonte": "Recursos Livres da Uniao",
                "codigo_gnd": "4",
                "gnd": "Investimentos",
                "codigo_modalidade": "90",
                "modalidade": "Aplicacoes Diretas",
                "codigo_elemento": "51",
                "elemento": "Obras e Instalacoes",
                "valor_pago": "0",
                "valor_empenhado": "0",
                "valor_liquidado": "0",
            },
        )

        return data_dir

    def test_gerador_gera_csvs_analiticos_normalizados(self):
        """A geração final deve separar dimensões, documentos e fatos."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            data_dir = self._criar_fontes_minimas(base)
            output_dir = data_dir / "csv"

            gerados = set(GeradorCSVs(data_dir=data_dir, output_dir=output_dir).executar())

            self.assertEqual(
                gerados,
                {
                    "dim_tempo.csv",
                    "dim_competencia_mensal.csv",
                    "dim_tipos_documento_fiscal.csv",
                    "dim_tipos_despesa.csv",
                    "dim_legislaturas_dep_federais.csv",
                    "dim_dep_federal.csv",
                    "dim_deputados_federais_referencia.csv",
                    "tb_documentos_despesas_deputados.csv",
                    "tb_despesas_deputados.csv",
                    "dim_senadores.csv",
                    "tb_documentos_despesas_senadores.csv",
                    "tb_despesas_senadores.csv",
                    "dim_regioes.csv",
                    "dim_estados.csv",
                    "dim_mesorregioes.csv",
                    "dim_microrregioes.csv",
                    "dim_regioes_intermediarias.csv",
                    "dim_regioes_imediatas.csv",
                    "dim_municipios.csv",
                    "dim_entes.csv",
                    "dim_funcao_siop.csv",
                    "dim_subfuncao_siop.csv",
                    "dim_programa.csv",
                    "dim_acao_siop.csv",
                    "dim_unidades_orcamentarias.csv",
                    "dim_fontes_recurso.csv",
                    "dim_gnds.csv",
                    "dim_modalidades_aplicacao.csv",
                    "dim_elementos_despesa.csv",
                    "tb_execucao_orcamentaria.csv",
                    "dim_fornecedores.csv",
                },
            )

            self.assertEqual(
                self._ler_csv(output_dir / "dim_tempo.csv")[1:],
                [["2025-03-09", "2025-03-09", "2025", "03", "09"], ["2025-04-10", "2025-04-10", "2025", "04", "10"]],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "dim_competencia_mensal.csv")[1:],
                [["2025-02", "2025", "02"], ["2025-03", "2025", "03"]],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "dim_dep_federal.csv")[1],
                ["123", "Deputado Exemplo", "ABC", "SP", "57"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "dim_deputados_federais_referencia.csv")[1],
                ["123", "Deputado Exemplo", "SP", "57", "57"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "tb_documentos_despesas_deputados.csv")[1],
                ["7514302", "12345678000190", "camara:0:nota_fiscal", "2025-04-10", "NF-29", "100.00"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "tb_despesas_deputados.csv")[1][1:6],
                ["7514302", "123", "57", "camara:combustivel", "2025-03"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "tb_documentos_despesas_senadores.csv")[1][1:],
                [
                    "07425595000176",
                    "senado::recibo",
                    "2025-03-09",
                    "112752",
                    "Pagamento de internet.",
                ],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "tb_despesas_senadores.csv")[1][1:],
                [
                    self._ler_csv(output_dir / "tb_documentos_despesas_senadores.csv")[1][0],
                    "22",
                    "senado:aluguel_de_imoveis_para_escritorio_politico",
                    "2025-02",
                    "281.58",
                ],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "dim_mesorregioes.csv")[1],
                ["1102", "Leste Rondoniense", "11"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "dim_municipios.csv")[1],
                ["1100015", "Alta Floresta D'Oeste", "11", "11006", "110005"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "dim_entes.csv")[1],
                ["3527207", "Lorena", "SP", "M", "0", "87468", "47563739000175"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "dim_subfuncao_siop.csv")[1],
                ["031", "Acao Legislativa", "01"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "dim_acao_siop.csv")[1],
                ["2024", "4061", "Processo Legislativo", "0034", "031"],
            )
            self.assertEqual(
                self._ler_csv(output_dir / "tb_execucao_orcamentaria.csv")[1],
                ["1177", "2024", "031", "0034", "4061", "01101", "1000", "4", "90", "51", "0", "0", "0"],
            )

            fornecedores = self._ler_csv(output_dir / "dim_fornecedores.csv")
            self.assertEqual(
                fornecedores[0],
                ["id_fornecedor", "documento", "tipo_documento", "cnpj_base", "nome_principal"],
            )
            self.assertEqual(len(fornecedores), 3)

    def test_gerador_falha_cedo_quando_a_extracao_esta_incompleta(self):
        """`gerar-csv` deve ser rejeitado antes de montar saídas parciais."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            data_dir = base / "data"
            self._escrever_jsonl(
                data_dir / "legislaturas.json",
                {"id": 57, "dataInicio": "2023-02-01", "dataFim": "2027-01-31"},
            )

            with self.assertRaises(UserInputError) as ctx:
                GeradorCSVs(data_dir=data_dir, output_dir=data_dir / "csv").executar()

        self.assertIn("deputados por legislatura da Camara", str(ctx.exception))
        self.assertIn("despesas CEAPS do Senado", str(ctx.exception))

    def test_gerador_executa_as_rotinas_registradas(self):
        """A fachada pública deve respeitar a ordem do registry em `utils.csv`."""

        chamadas = []

        def _rotina_a(data_dir: Path, output_dir: Path) -> list[str]:
            chamadas.append(("a", data_dir, output_dir))
            return ["a.csv"]

        def _rotina_b(data_dir: Path, output_dir: Path) -> list[str]:
            chamadas.append(("b", data_dir, output_dir))
            return ["b.csv"]

        rotinas = (
            SimpleNamespace(nome="a", fontes_obrigatorias=(), executar=_rotina_a),
            SimpleNamespace(nome="b", fontes_obrigatorias=(), executar=_rotina_b),
        )

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            with patch("utils.csv.ROTINAS_CSV", rotinas):
                gerados = GeradorCSVs(
                    data_dir=base / "data",
                    output_dir=base / "csv",
                ).executar()

        self.assertEqual(gerados, ["a.csv", "b.csv"])
        self.assertEqual(
            chamadas,
            [
                ("a", base / "data", base / "csv"),
                ("b", base / "data", base / "csv"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
