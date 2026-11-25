"""Baixa a amostra de estados e converte automaticamente para Parquet."""

import logging

from icsap.config import ANOS
from icsap.extract.sih import baixar_tudo
from icsap.transform.limpeza import converter_tudo

logger = logging.getLogger(__name__)

# Amostra representativa: cobre ~70% das internações do país
AMOSTRA = ["SP", "MG", "RJ", "RS", "PR", "GO", "AM", "PA", "SC", "ES"]


def executar() -> None:
    """Baixa a amostra e converte tudo o que estiver em raw."""
    logger.info("=== baixando amostra de %d estados ===", len(AMOSTRA))
    logger.info("estados: %s", ", ".join(AMOSTRA))
    logger.info("anos: %s", ANOS)

    baixar_tudo(ufs=AMOSTRA, anos=ANOS)
    logger.info("download concluído")

    logger.info("=== convertendo DBC para Parquet ===")
    converter_tudo()

    logger.info("=== pronto ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    executar()