"""Comparação dos grupos ICSAP entre Bahia e Nordeste."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from icsap.comparacao_grupos import comparar_grupos
from icsap.config import PROCESSED_DIR
from icsap.rotulos import LEGENDA, ROTULOS

logger = logging.getLogger(__name__)


def _rotulo(n) -> str:
    """Encurta o nome do grupo para caber no eixo."""
    if pd.isna(n):
        return "—"
    texto = str(n)
    return texto if len(texto) <= 38 else texto[:35] + "..."


def gerar_grafico(base=None) -> None:
    """Gera o gráfico de barras comparando BA e NE por grupo."""
    if base is None:
        from icsap.analise import carregar_base_unica
        base = carregar_base_unica()

    dados = comparar_grupos(base)

    if dados.empty:
        logger.error("nenhum grupo encontrado para o gráfico")
        return

    dados = dados[dados["nome"].notna()].copy()

    if dados.empty:
        logger.error("todos os grupos vieram sem nome")
        return

    dados["rotulo"] = dados["nome"].apply(_rotulo)

    dados = dados.sort_values("diferenca_pp", ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(12, 8))

    y = np.arange(len(dados))
    altura = 0.38

    ax.barh(
        y + altura / 2, dados["taxa_ba_pct"], height=altura,
        color="#c0392b", label="Bahia",
    )
    ax.barh(
        y - altura / 2, dados["taxa_ne_pct"], height=altura,
        color="#7f8c8d", label="Nordeste",
    )

    for i, r in dados.iterrows():
        ax.text(
            r["taxa_ba_pct"] + 0.05, i + altura / 2,
            f"{r['taxa_ba_pct']:.2f}",
            va="center", fontsize=8, color="#c0392b",
        )
        ax.text(
            r["taxa_ne_pct"] + 0.05, i - altura / 2,
            f"{r['taxa_ne_pct']:.2f}",
            va="center", fontsize=8, color="#555555",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(dados["rotulo"], fontsize=9)
    ax.set_xlabel(f"{ROTULOS['ICSAP']} (%)", fontsize=12, labelpad=10)
    ax.set_title(
        "Grupos ICSAP — Bahia vs Nordeste",
        fontsize=13, fontweight="bold", pad=14,
    )
    ax.legend(fontsize=10, loc="lower right")
    ax.grid(True, axis="x", alpha=0.3)
    ax.invert_yaxis()

    plt.subplots_adjust(bottom=0.22, left=0.34, right=0.95, top=0.93)

    fig.text(
        0.5, 0.015, LEGENDA,
        ha="center", va="bottom",
        fontsize=8, style="italic", color="#555555",
        wrap=True,
        bbox=dict(
            boxstyle="round,pad=0.6",
            facecolor="white",
            edgecolor="#dddddd",
            linewidth=0.8,
            alpha=1.0,
        ),
    )

    destino = PROCESSED_DIR / "grupos_ba_nordeste.png"
    plt.savefig(destino, dpi=150, facecolor="white")
    logger.info("gráfico salvo em %s", destino)
    plt.close(fig)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    gerar_grafico()