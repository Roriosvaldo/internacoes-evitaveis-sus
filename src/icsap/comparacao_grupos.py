"""Comparação da taxa de ICSAP por grupo entre Bahia e Nordeste."""

import gc
import logging

import pandas as pd

from icsap.config import UFS_NORDESTE

logger = logging.getLogger(__name__)

__all__ = ["comparar_grupos"]


def _base_grupo_uf_ano(base: pd.DataFrame) -> pd.DataFrame:
    """Agrega por grupo, UF e ano. Aceita base bruta ou já agregada.

    Filtra em etapas para não alocar um array de 57 milhões de posições
    de uma vez — evita MemoryError em bases grandes.
    """
    if "taxa_icsap_pct" in base.columns and "UF" in base.columns:
        return base.loc[
            base["UF"].notna(),
            ["UF", "ANO", "ICSAP_GRUPO", "ICSAP_NOME",
             "internacoes_total", "internacoes_icsap"],
        ]

    # etapa 1: só as linhas classificadas como ICSAP (~17% do total)
    mask_icsap = base["ICSAP"] == 1
    sub = base.loc[mask_icsap, ["UF", "ANO", "ICSAP_GRUPO", "ICSAP_NOME", "ICSAP"]]

    # etapa 2: agrega por grupo/UF/ano
    icsap_por_grupo = (
        sub.groupby(["UF", "ANO", "ICSAP_GRUPO", "ICSAP_NOME"], dropna=False)
        .agg(internacoes_icsap=("ICSAP", "sum"))
        .reset_index()
    )
    del sub
    gc.collect()

    # etapa 3: total geral por UF/ano (denominador), direto da base
    total_por_uf = (
        base.loc[base["UF"].notna(), ["UF", "ANO"]]
        .groupby(["UF", "ANO"], dropna=False)
        .size()
        .reset_index(name="internacoes_total")
    )

    return icsap_por_grupo.merge(
        total_por_uf, on=["UF", "ANO"], how="left"
    )


def _total_geral_uf_ano(bruto: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Total geral de internações por UF no ano.

    O `bruto` já traz `internacoes_total` por UF/ano (denominador real),
    então basta pegar uma linha por UF — não somar por grupo.
    """
    sub = bruto.loc[bruto["ANO"] == ano, ["UF", "internacoes_total"]]
    return sub.drop_duplicates(subset=["UF"]).reset_index(drop=True)


def comparar_grupos(base: pd.DataFrame, ano: int | None = None) -> pd.DataFrame:
    """Compara a taxa por grupo entre BA e média do Nordeste."""
    bruto = _base_grupo_uf_ano(base)

    if bruto.empty:
        logger.warning("nenhum grupo válido na base")
        return pd.DataFrame()

    if ano is None:
        ano = int(bruto["ANO"].max())

    sub = bruto.loc[bruto["ANO"] == ano]

    # total geral por UF no ano (denominador correto)
    totais = _total_geral_uf_ano(bruto, ano)

    # BA por grupo
    ba = (
        sub.loc[sub["UF"] == "BA"]
        .groupby(["ICSAP_GRUPO", "ICSAP_NOME"], dropna=False)
        .agg(icsap_ba=("internacoes_icsap", "sum"))
        .reset_index()
    )
    total_ba = int(totais.loc[totais["UF"] == "BA", "internacoes_total"].sum())
    ba["total_ba"] = total_ba

    # Nordeste por grupo (todos os estados exceto BA)
    ne_ufs = [u for u in UFS_NORDESTE if u != "BA"]
    ne = (
        sub.loc[sub["UF"].isin(ne_ufs)]
        .groupby(["ICSAP_GRUPO", "ICSAP_NOME"], dropna=False)
        .agg(icsap_ne=("internacoes_icsap", "sum"))
        .reset_index()
    )
    total_ne = int(totais.loc[totais["UF"].isin(ne_ufs), "internacoes_total"].sum())
    ne["total_ne"] = total_ne

    if ba.empty or ne.empty:
        logger.warning("dados insuficientes para comparar grupos")
        return pd.DataFrame()

    merged = ba.merge(ne, on=["ICSAP_GRUPO", "ICSAP_NOME"], how="inner")

    # remove grupo fantasma (nome nulo)
    merged = merged.loc[merged["ICSAP_NOME"].notna()].reset_index(drop=True)

    if merged.empty:
        logger.warning("nenhum grupo com nome válido após o merge")
        return pd.DataFrame()

    merged["taxa_ba_pct"] = (
        merged["icsap_ba"] / merged["total_ba"] * 100
    ).round(2)
    merged["taxa_ne_pct"] = (
        merged["icsap_ne"] / merged["total_ne"] * 100
    ).round(2)
    merged["diferenca_pp"] = (
        merged["taxa_ba_pct"] - merged["taxa_ne_pct"]
    ).round(2)
    merged["diferenca_rel_pct"] = (
        merged["diferenca_pp"] / merged["taxa_ne_pct"] * 100
    ).round(1)

    merged["nome"] = merged["ICSAP_NOME"]
    merged["ano"] = ano

    return (
        merged[[
            "ICSAP_GRUPO", "nome", "ano",
            "taxa_ba_pct", "taxa_ne_pct",
            "diferenca_pp", "diferenca_rel_pct",
            "total_ba", "icsap_ba", "total_ne", "icsap_ne",
        ]]
        .sort_values("diferenca_pp", ascending=False)
        .reset_index(drop=True)
    )