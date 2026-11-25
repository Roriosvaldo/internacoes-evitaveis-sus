"""Baixa a amostra de estados e converte automaticamente para Parquet."""

import logging

from icsap.config import ANOS, UFS_NORDESTE
from icsap.sih import baixar_tudo
from icsap.limpeza import converter_tudo

logger = logging.getLogger(__name__)

# Amostra: os 10 maiores por volume + todo o Nordeste (foco da análise)
_TOP_VOLUME = ["SP", "MG", "RJ", "RS", "PR", "GO", "AM", "PA", "SC", "ES"]

AMOSTRA = sorted(set(_TOP_VOLUME) | set(UFS_NORDESTE))

__all__ = ["AMOSTRA", "executar"]


def executar() -> None:
    """Baixa a amostra e converte tudo o que estiver em raw."""
    logger.info("=== baixando amostra de %d estados ===", len(AMOSTRA))
    logger.info("estados: %s", ", ".join(AMOSTRA))

    baixar_tudo(ufs=AMOSTRA, anos=ANOS)

    logger.info("=== convertendo raw para parquet ===")
    converter_tudo()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    executar()