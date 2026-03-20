"""Fachada publica e orquestracao unica da geracao de CSVs analiticos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from configuracao.logger import logger
from infra.errors import UserInputError

from .camara import FONTES_OBRIGATORIAS as FONTES_CAMARA
from .camara import gerar_csvs_camara
from .comum import FonteObrigatoria
from .despesas import FONTES_OBRIGATORIAS as FONTES_DESPESAS_COMPARTILHADAS
from .despesas import gerar_csvs_despesas_compartilhadas
from .ibge import FONTES_OBRIGATORIAS as FONTES_IBGE
from .ibge import gerar_csvs_ibge
from .portal import gerar_csvs_portal
from .senado import FONTES_OBRIGATORIAS as FONTES_SENADO
from .senado import gerar_csvs_senado
from .siconfi import FONTES_OBRIGATORIAS as FONTES_SICONFI
from .siconfi import gerar_csvs_siconfi
from .siop import FONTES_OBRIGATORIAS as FONTES_SIOP
from .siop import gerar_csvs_siop


@dataclass(frozen=True)
class RotinaCSV:
    """Agrupa validacao e geracao de uma rotina de CSVs."""

    nome: str
    fontes_obrigatorias: tuple[FonteObrigatoria, ...]
    executar: Callable[[Path, Path], list[str]]


ROTINAS_CSV = (
    RotinaCSV("despesas_compartilhadas", FONTES_DESPESAS_COMPARTILHADAS, gerar_csvs_despesas_compartilhadas),
    RotinaCSV("camara", FONTES_CAMARA, gerar_csvs_camara),
    RotinaCSV("senado", FONTES_SENADO, gerar_csvs_senado),
    RotinaCSV("ibge", FONTES_IBGE, gerar_csvs_ibge),
    RotinaCSV("siconfi", FONTES_SICONFI, gerar_csvs_siconfi),
    RotinaCSV("siop", FONTES_SIOP, gerar_csvs_siop),
    RotinaCSV("portal", (), gerar_csvs_portal),
)


class GeradorCSVs:
    """Executa a camada analitica final depois que as extracoes terminarem."""

    def __init__(
        self,
        data_dir: str | Path = "data",
        output_dir: str | Path = "data/csv",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)

    def validar_fontes(self) -> None:
        """Falha cedo quando a extracao base ainda nao terminou."""

        faltando: list[str] = []

        for rotina in ROTINAS_CSV:
            for fonte in rotina.fontes_obrigatorias:
                if any(self.data_dir.glob(fonte.padrao)):
                    continue
                faltando.append(
                    f"- {rotina.nome}: {fonte.descricao} ({self.data_dir / fonte.padrao})"
                )

        if faltando:
            detalhes = "\n".join(faltando)
            raise UserInputError(
                "O comando `gerar-csv` so deve ser executado apos o termino das "
                "extracoes base. Artefatos ausentes:\n"
                f"{detalhes}"
            )

    def executar(self) -> list[str]:
        """Gera todos os CSVs finais na camada analitica normalizada."""

        self.validar_fontes()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        gerados: list[str] = []
        logger.info("=== INICIANDO GERACAO DE CSVS ANALITICOS ===")

        for rotina in ROTINAS_CSV:
            logger.info("--- Gerando CSVs de %s ---", rotina.nome)
            gerados.extend(rotina.executar(self.data_dir, self.output_dir))

        logger.info("=== GERACAO DE CSVS ANALITICOS FINALIZADA | arquivos=%s ===", len(gerados))
        return gerados


def executar_geracao_csv(
    data_dir: str | Path = "data",
    output_dir: str | Path = "data/csv",
) -> list[str]:
    """Atalho funcional para a geracao completa da camada CSV."""

    return GeradorCSVs(data_dir=data_dir, output_dir=output_dir).executar()


__all__ = ["GeradorCSVs", "ROTINAS_CSV", "executar_geracao_csv"]
