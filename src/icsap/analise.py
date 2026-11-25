"""Carregamento e preparação da base de internações do SIH/SUS."""

import gc
import logging
import re

import pandas as pd

from icsap.classificacao_icsap import classificar_dataframe
from icsap.config import ANOS as ANOS_PADRAO
from icsap.config import INTERIM_DIR

logger = logging.getLogger(__name__)

__all__ = [
    "carregar_base_unica",
    "preparar",
    "carregar_ano",
    "agregar_base",
]

COLUNAS_ESSENCIAIS = [
    "MUNIC_RES",
    "DIAG_PRINC",
    "N_AIH",
    "MORTE",
    "VAL_TOT",
    "ANO",
]

MAPA_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
    "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
    "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
    "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
    "52": "GO", "53": "DF",
}


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara a base: garante UF, ANO e tipos corretos.

    Não copia o DataFrame inteiro — adiciona colunas no lugar.
    """
    if df.empty:
        return df

    if "UF" not in df.columns and "MUNIC_RES" in df.columns:
        codigos = df["MUNIC_RES"].astype(str).str.zfill(6).str[:2]
        df["UF"] = codigos.map(MAPA_UF)

    # ANO_CMPT é a coluna real do DATASUS
    if "ANO" not in df.columns:
        if "ANO_CMPT" in df.columns:
            df["ANO"] = pd.to_numeric(df["ANO_CMPT"], errors="coerce")
        elif "DT_INTER" in df.columns:
            df["ANO"] = pd.to_datetime(
                df["DT_INTER"], errors="coerce", dayfirst=True
            ).dt.year

    if "ANO" in df.columns:
        df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce").astype("Int64")

    if "MORTE" in df.columns:
        df["MORTE"] = (
            pd.to_numeric(df["MORTE"], errors="coerce")
            .fillna(0)
            .astype("int8")
        )

    if "VAL_TOT" in df.columns:
        df["VAL_TOT"] = pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0.0)

    return df


def _extrair_ano(nome_arquivo: str) -> int | None:
    """Extrai o ano do nome do arquivo DATASUS.

    Padrão: RD + UF + AAMM (ex.: RDAL2001 = AL, 2020, mês 01).
    """
    match = re.search(r"(\d{2})(\d{2})$", nome_arquivo)
    if not match:
        return None

    aa = int(match.group(1))
    return 2000 + aa


def _ler_arquivos(lista) -> pd.DataFrame:
    """Lê e concatena uma lista de parquets, ignorando falhas."""
    pedacos = []
    for arq in lista:
        try:
            pedacos.append(pd.read_parquet(arq))
        except Exception as exc:
            logger.warning("falha ao ler %s: %s", arq.name, exc)

    if not pedacos:
        return pd.DataFrame()

    df = pd.concat(pedacos, ignore_index=True)
    del pedacos
    gc.collect()

    return df


def carregar_ano(ano: int) -> pd.DataFrame:
    """Carrega e classifica todos os arquivos de um ano.

    O nome do arquivo usa AAMM, então o glob precisa de dois dígitos.
    """
    arquivos = sorted(INTERIM_DIR.glob(f"*{ano % 100:02d}*.parquet"))

    if not arquivos:
        logger.warning("nenhum arquivo encontrado para o ano %d", ano)
        return pd.DataFrame()

    logger.info("ano %d: %d arquivos", ano, len(arquivos))

    df = _ler_arquivos(arquivos)

    if df.empty:
        return df

    df = preparar(df)

    if "ANO" not in df.columns:
        logger.warning("ano %d: coluna ANO ausente após preparar", ano)
        return pd.DataFrame()

    mask = df["ANO"] == ano
    if not mask.any():
        logger.warning("ano %d sem registros após filtro", ano)
        return pd.DataFrame()

    df = df.loc[mask].reset_index(drop=True)

    df = classificar_dataframe(df, coluna="DIAG_PRINC")

    logger.info("ano %d concluído: %d internações", ano, len(df))

    return df


def carregar_base_unica(anos: list[int] | None = None) -> pd.DataFrame:
    """Carrega e classifica a base processada, ano a ano.

    Processar por ano reduz o pico de memória: cada ano é lido,
    filtrado e classificado antes do próximo entrar em memória.
    """
    if anos is None:
        anos = ANOS_PADRAO

    arquivos = sorted(INTERIM_DIR.glob("*.parquet"))

    if not arquivos:
        raise FileNotFoundError(f"nenhum parquet encontrado em {INTERIM_DIR}")

    logger.info("carregando %d arquivos parquet", len(arquivos))

    partes = []
    total = 0
    anos_lidos: set[int] = set()

    for i, arq in enumerate(arquivos, 1):
        try:
            df = pd.read_parquet(arq)
        except Exception as exc:
            logger.warning("falha ao ler %s: %s", arq.name, exc)
            continue

        if df.empty:
            continue

        # preparar PRIMEIRO, para criar a coluna ANO
        df = preparar(df)

        if "ANO" not in df.columns:
            logger.warning("%s sem ano identificável — ignorado", arq.name)
            del df
            continue

        # filtro otimizado: evita a cópia profunda que trava no Ctrl+C
        mask = df["ANO"].isin(anos)
        if not mask.any():
            del df
            continue

        df = df.loc[mask].reset_index(drop=True)

        df = classificar_dataframe(df, coluna="DIAG_PRINC")

        partes.append(df)
        total += len(df)
        anos_lidos.update(df["ANO"].dropna().astype(int).unique())

        if i % 50 == 0 or i == len(arquivos):
            logger.info(
                "lidos %d/%d arquivos — %d internações acumuladas",
                i, len(arquivos), total,
            )

        del df
        if i % 100 == 0:
            gc.collect()

    if not partes:
        raise ValueError(
            f"nenhum dado para os anos {sorted(anos)} — "
            f"verifique a coluna ANO_CMPT nos parquets"
        )

    base = pd.concat(partes, ignore_index=True)
    del partes
    gc.collect()

    logger.info(
        "base carregada: %d internações (anos: %s)",
        len(base), sorted(anos_lidos),
    )

    return base

def agregar_base(base: pd.DataFrame) -> pd.DataFrame:
    """Agrega a base bruta por UF, ANO e grupo ICSAP.

    Reduz 57 milhões de linhas para ~1.000, permitindo que as análises
    rodem sem estourar memória.
    """
    if base.empty:
        return base

    # já agregada
    if "taxa_icsap_pct" in base.columns:
        return base

    colunas = ["UF", "ANO", "ICSAP_GRUPO", "ICSAP_NOME", "ICSAP"]
    faltando = [c for c in colunas if c not in base.columns]
    if faltando:
        raise ValueError(f"colunas ausentes para agregar: {faltando}")

    # filtra só as linhas classificadas como ICSAP (~17%)
    mask = base["ICSAP"] == 1
    sub = base.loc[mask, colunas]

    icsap_por_grupo = (
        sub.groupby(["UF", "ANO", "ICSAP_GRUPO", "ICSAP_NOME"], dropna=False)
        .agg(internacoes_icsap=("ICSAP", "sum"))
        .reset_index()
    )
    del sub
    gc.collect()

    # total por UF/ano (denominador)
    total_por_uf = (
        base.loc[base["UF"].notna(), ["UF", "ANO"]]
        .groupby(["UF", "ANO"], dropna=False)
        .size()
        .reset_index(name="internacoes_total")
    )

    agregado = icsap_por_grupo.merge(
        total_por_uf, on=["UF", "ANO"], how="left"
    )

    agregado["taxa_icsap_pct"] = (
        agregado["internacoes_icsap"] / agregado["internacoes_total"] * 100
    ).round(3)

    logger.info(
        "base agregada: %d linhas (de %d)",
        len(agregado), len(base),
    )

    return agregado