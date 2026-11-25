"""Roda a pipeline completa: download, conversão, comparações e exportação."""

import gc
import logging
import sys
import time

from icsap.analise import agregar_base, carregar_base_unica
from icsap.baixar_amostra import executar as baixar_amostra
from icsap.comparacao_grupos import comparar_grupos
from icsap.comparacao_regional import comparar, ranking_estados
from icsap.exportar import executar as exportar
from icsap.grafico_comparacao import gerar_grafico as graf_evolucao
from icsap.grafico_convergencia import gerar_grafico as graf_convergencia
from icsap.relatorio import gerar_relatorio

logger = logging.getLogger(__name__)


def _etapa(nome: str, funcao) -> bool:
    """Executa uma etapa e reporta sucesso ou falha."""
    logger.info("\n" + "=" * 60)
    logger.info("ETAPA: %s", nome)
    logger.info("=" * 60)
    inicio = time.time()
    try:
        funcao()
    except Exception as exc:
        logger.error("falhou em '%s': %s", nome, exc, exc_info=True)
        return False
    logger.info("concluída em %.1fs", time.time() - inicio)
    return True


def _analises(base) -> None:
    """Agrega a base uma vez e roda todas as análises sobre o agregado."""
    logger.info("agregando base (57M → ~1k linhas)")
    agregado = agregar_base(base)

    # libera a base bruta — não é mais necessária
    del base
    gc.collect()

    logger.info("comparação regional")
    comp = comparar(agregado)
    if comp.empty:
        raise RuntimeError("comparação regional vazia")

    logger.info("ranking dos estados")
    ranking = ranking_estados(agregado)

    logger.info("comparação por grupo")
    grupos = comparar_grupos(agregado)

    logger.info("gerando gráficos")
    graf_evolucao(agregado)
    graf_convergencia(agregado)
    graf_grupos(agregado)

    logger.info("exportando CSV")
    exportar(comp, ranking, grupos)

    logger.info("gerando relatório")
    gerar_relatorio(agregado)


def executar(baixar: bool = True) -> None:
    """Roda a pipeline inteira, parando na primeira falha."""
    if baixar:
        if not _etapa("download e conversão da amostra", baixar_amostra):
            logger.error("pipeline interrompida no download")
            sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("ETAPA: carregamento da base")
    logger.info("=" * 60)
    inicio = time.time()
    try:
        base = carregar_base_unica()
    except Exception as exc:
        logger.error("falhou ao carregar a base: %s", exc, exc_info=True)
        sys.exit(1)
    logger.info("concluída em %.1fs", time.time() - inicio)

    if not _etapa("análises e exportação", lambda: _analises(base)):
        logger.error("pipeline interrompida nas análises")
        sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE CONCLUÍDA")
    logger.info("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    baixar = "--sem-download" not in sys.argv
    executar(baixar=baixar)