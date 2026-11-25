"""Comparação da taxa de ICSAP entre Bahia, Nordeste e Brasil."""

import logging

import pandas as pd

from icsap.config import UFS_NORDESTE

logger = logging.getLogger(__name__)

UF_BAHIA = "BA"

SIGLAS = {
    "RO": "Rondônia", "AC": "Acre", "AM": "Amazonas", "RR": "Roraima",
    "PA": "Pará", "AP": "Amapá", "TO": "Tocantins", "MA": "Maranhão",
    "PI": "Piauí", "CE": "Ceará", "RN": "Rio Grande do Norte",
    "PB": "Paraíba", "PE": "Pernambuco", "AL": "Alagoas",
    "SE": "Sergipe", "BA": "Bahia", "MG": "Minas Gerais",
    "ES": "Espírito Santo", "RJ": "Rio de Janeiro", "SP": "São Paulo",
    "PR": "Paraná", "SC": "Santa Catarina", "RS": "Rio Grande do Sul",
    "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "GO": "Goiás",
    "DF": "Distrito Federal",
}

__all__ = [
    "comparar", "ranking_estados", "UF_BAHIA", "sigla_uf", "SIGLAS",
    "UFS_NORDESTE",
]


def sigla_uf(nome: str) -> str:
    """Converte nome do estado em sigla. Aceita sigla e devolve igual."""
    nome = str(nome).strip()

    if len(nome) == 2 and nome.upper() in SIGLAS:
        return nome.upper()

    for sigla, completo in SIGLAS.items():
        if completo.lower() == nome.lower():
            return sigla

    return nome.upper()


def _agregar_uf_ano(base: pd.DataFrame) -> pd.DataFrame:
    """Agrega por UF e ano. Aceita base bruta ou já agregada."""
    if "taxa_icsap_pct" in base.columns and "UF" in base.columns:
        return (
            base.groupby(["UF", "ANO"], dropna=False)
            .agg(
                internacoes_total=("internacoes_total", "sum"),
                internacoes_icsap=("internacoes_icsap", "sum"),
                obitos=("obitos", "sum"),
                valor_total=("valor_total", "sum"),
            )
            .reset_index()
        )

    return (
        base.groupby(["UF", "ANO"], dropna=False)
        .agg(
            internacoes_total=("N_AIH", "size"),
            internacoes_icsap=("ICSAP", "sum"),
            obitos=("MORTE", "sum"),
            valor_total=("VAL_TOT", "sum"),
        )
        .reset_index()
    )


def comparar(base: pd.DataFrame) -> pd.DataFrame:
    """Compara a taxa da BA com a média do Nordeste e a média nacional."""
    uf_ano = _agregar_uf_ano(base)
    uf_ano = uf_ano[uf_ano["UF"].notna()]

    if uf_ano.empty:
        logger.warning("nenhuma UF válida na base")
        return pd.DataFrame()

    uf_ano["taxa_icsap_pct"] = (
        uf_ano["internacoes_icsap"] / uf_ano["internacoes_total"] * 100
    ).round(2)

    linhas = []

    ba = uf_ano[uf_ano["UF"] == UF_BAHIA]
    for _, r in ba.iterrows():
        linhas.append({
            "ANO": int(r["ANO"]),
            "escopo": "Bahia",
            "internacoes_total": int(r["internacoes_total"]),
            "internacoes_icsap": int(r["internacoes_icsap"]),
            "taxa_icsap_pct": float(r["taxa_icsap_pct"]),
        })

    ne = uf_ano[uf_ano["UF"].isin(UFS_NORDESTE)]
    for ano, sub in ne.groupby("ANO"):
        total = sub["internacoes_total"].sum()
        icsap = sub["internacoes_icsap"].sum()
        linhas.append({
            "ANO": int(ano),
            "escopo": "Nordeste (média)",
            "internacoes_total": int(total),
            "internacoes_icsap": int(icsap),
            "taxa_icsap_pct": round(icsap / total * 100, 2) if total else 0.0,
        })

    for ano, sub in uf_ano.groupby("ANO"):
        total = sub["internacoes_total"].sum()
        icsap = sub["internacoes_icsap"].sum()
        linhas.append({
            "ANO": int(ano),
            "escopo": "Brasil (média)",
            "internacoes_total": int(total),
            "internacoes_icsap": int(icsap),
            "taxa_icsap_pct": round(icsap / total * 100, 2) if total else 0.0,
        })

    return pd.DataFrame(linhas).sort_values(["ANO", "escopo"]).reset_index(drop=True)


def ranking_estados(
    base: pd.DataFrame,
    ano: int | None = None,
    retornar_descartadas: bool = False,
):
    """Ranking dos estados por taxa de ICSAP no ano mais recente.

    Se `retornar_descartadas=True`, devolve (ranking, lista_de_ufs_descartadas).
    """
    uf_ano = _agregar_uf_ano(base)
    uf_ano = uf_ano[uf_ano["UF"].notna()]

    if uf_ano.empty:
        return (pd.DataFrame(), []) if retornar_descartadas else pd.DataFrame()

    mediana = uf_ano["internacoes_total"].median()
    completas = uf_ano[uf_ano["internacoes_total"] >= mediana * 0.2]

    descartadas = sorted(set(uf_ano["UF"]) - set(completas["UF"]))
    if descartadas:
        logger.info(
            "ranking: descartadas %d UFs com dados parciais: %s",
            len(descartadas), ", ".join(descartadas),
        )

    if ano is None:
        ano = int(completas["ANO"].max())

    sub = completas[completas["ANO"] == ano].copy()
    sub["taxa_icsap_pct"] = (
        sub["internacoes_icsap"] / sub["internacoes_total"] * 100
    ).round(2)
    sub["ano"] = ano

    ranking = (
        sub[["UF", "ano", "internacoes_total", "internacoes_icsap", "taxa_icsap_pct"]]
        .sort_values("taxa_icsap_pct", ascending=False)
        .reset_index(drop=True)
    )

    if retornar_descartadas:
        return ranking, descartadas
    return ranking