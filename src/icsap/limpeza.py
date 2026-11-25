"""Converte DBC para Parquet, só anos com os 12 meses completos."""

import logging
from pathlib import Path

import pandas as pd
from dbfread import DBF

from icsap.config import ANOS, INTERIM_DIR, RAW_DIR, UFS_AMOSTRA
from icsap.sih import MESES, nome_arquivo, verificar_cobertura

logger = logging.getLogger(__name__)


def _ler_dbc(caminho: Path) -> pd.DataFrame:
    """Lê um DBC do DATASUS e devolve um DataFrame."""
    tabela = DBF(str(caminho), encoding="latin-1", ignore_missing_memofile=True)
    return pd.DataFrame(iter(tabela))


def _converter_arquivo(caminho: Path) -> Path | None:
    """Converte um DBC em parquet no interim. Retorna o destino ou None."""
    destino = INTERIM_DIR / f"{caminho.stem}.parquet"

    if destino.exists() and destino.stat().st_size > 0:
        logger.debug("já convertido, pulando: %s", destino.name)
        return destino

    try:
        df = _ler_dbc(caminho)
    except Exception as exc:
        logger.error("falhou ao ler %s: %s", caminho.name, exc)
        return None

    df.to_parquet(destino, index=False)
    logger.info("convertido: %s (%d linhas)", caminho.name, len(df))
    return destino


def converter_tudo() -> None:
    """Converte DBC para Parquet, só UFs/anos com os 12 meses completos."""
    total_ok = 0
    total_pulados = 0
    pares_pulados = []

    for uf in UFS_AMOSTRA:
        for ano in ANOS:
            meses_presentes = verificar_cobertura(uf, ano)

            if meses_presentes < 12:
                logger.warning(
                    "pulando %s/%d: apenas %d de 12 meses no raw",
                    uf, ano, meses_presentes,
                )
                pares_pulados.append((uf, ano, meses_presentes))
                total_pulados += 1
                continue

            logger.info("convertendo %s/%d (12 meses completos)", uf, ano)

            for mes in MESES:
                caminho = RAW_DIR / nome_arquivo(uf, ano, mes)
                if not caminho.exists():
                    continue

                if _converter_arquivo(caminho):
                    total_ok += 1

    logger.info("=== conversão concluída ===")
    logger.info("convertidos: %d arquivos", total_ok)
    logger.info("pares UF/ano pulados: %d", total_pulados)

    if pares_pulados:
        logger.info("detalhe dos pulados:")
        for uf, ano, n in pares_pulados:
            logger.info("  %s/%d: %d meses", uf, ano, n)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    converter_tudo()