"""Exporta os resultados da análise em CSV."""

import logging

import pandas as pd

from icsap.config import PROCESSED_DIR

logger = logging.getLogger(__name__)


def executar(comp: pd.DataFrame, ranking: pd.DataFrame,
             grupos: pd.DataFrame) -> None:
    """Grava as três tabelas em CSV, recebendo-as já prontas.

    A assinatura mudou: antes a função lia os parquet do disco. Agora
    recebe as tabelas em memória, para o pipeline não reler a base.
    """
    if comp is None or comp.empty:
        logger.warning("comparação regional vazia — nada a exportar")
        return

    destino_comp = PROCESSED_DIR / "comparacao_regional.csv"
    comp.to_csv(destino_comp, index=False, encoding="utf-8-sig")
    logger.info("gravado: %s (%d linhas)", destino_comp.name, len(comp))

    if ranking is not None and not ranking.empty:
        destino_rank = PROCESSED_DIR / "ranking_estados.csv"
        ranking.to_csv(destino_rank, index=False, encoding="utf-8-sig")
        logger.info("gravado: %s (%d linhas)", destino_rank.name, len(ranking))
    else:
        logger.warning("ranking vazio — CSV não gerado")

    if grupos is not None and not grupos.empty:
        destino_grupos = PROCESSED_DIR / "grupos_icsap.csv"
        grupos.to_csv(destino_grupos, index=False, encoding="utf-8-sig")
        logger.info("gravado: %s (%d linhas)", destino_grupos.name, len(grupos))
    else:
        logger.warning("grupos vazios — CSV não gerado")


if __name__ == "__main__":
    # execução isolada: carrega a base e exporta
    from icsap.analise import carregar_base_unica
    from icsap.comparacao_grupos import comparar_grupos
    from icsap.comparacao_regional import comparar, ranking_estados

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    base = carregar_base_unica()
    executar(comparar(base), ranking_estados(base), comparar_grupos(base))