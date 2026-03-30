"""Testes do fluxo sequencial da pipeline da Camara."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from pipeline import PipelineCamara


class PipelineCamaraTestCase(unittest.TestCase):
    """Garante que a pipeline da Camara nao gere CSV no meio da extracao."""

    def test_pipeline_camara_executa_apenas_as_etapas_de_extracao(self):
        """A consolidação CSV deve ficar fora da pipeline e no comando dedicado."""

        with patch("pipeline.Legislatura") as legislatura_cls:
            with patch("pipeline.DeputadosLegislatura") as deputados_cls:
                with patch("pipeline.Despesas") as despesas_cls:
                    with patch(
                        "pipeline.obter_configuracao_endpoint",
                        return_value={"endpoint": "deputados/{id}/despesas"},
                    ):
                        PipelineCamara(ano_inicio=2023, ano_fim=2026).executar()

        legislatura_cls.assert_called_once_with()
        legislatura_cls.return_value.executar.assert_called_once_with()
        deputados_cls.assert_called_once_with()
        deputados_cls.return_value.executar.assert_called_once_with()
        despesas_cls.assert_called_once_with(
            "deputados_despesas",
            {"endpoint": "deputados/{id}/despesas"},
        )
        despesas_cls.return_value.executar.assert_called_once_with(
            ano_inicio=2023,
            ano_fim=2026,
        )


if __name__ == "__main__":
    unittest.main()
