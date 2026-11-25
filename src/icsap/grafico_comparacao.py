"""Gera gráfico da evolução da taxa de ICSAP: BA, Nordeste e Brasil."""

import logging

import matplotlib.pyplot as plt

from icsap.comparacao_regional import comparar
from icsap.config import PROCESSED_DIR
from icsap.rotulos import ROTULOS, LEGENDA

logger = logging.getLogger(__name__)

ESTILOS = {
    "Brasil (média)": dict(color="#2c3e50", marker="^", linewidth=1.8,
                           linestyle=":", label="Brasil (média)"),
    "Nordeste (média)": dict(color="#7f8c8d", marker="o", linewidth=2,
                             linestyle="--", label="Nordeste (média)"),
    "Bahia": dict(color="#c0392b", marker="s", linewidth=2.5,
                  linestyle="-", label="Bahia"),
}


def gerar_grafico(base=None) -> None:
    """Plota a evolução anual da taxa de ICSAP por escopo.

    Se `base` for fornecida, não relê os arquivos parquet.
    """
    comp = comparar(base)

    if comp.empty:
        logger.error("comparação vazia — nada a plotar")
        return

    pivot = comp.pivot_table(
        index="ANO", columns="escopo", values="taxa_icsap_pct"
    )

    fig, ax = plt.subplots(figsize=(11, 7))

    plotadas = []
    for escopo, estilo in ESTILOS.items():
        if escopo in pivot.columns:
            ax.plot(pivot.index, pivot[escopo], **estilo)
            plotadas.append(escopo)

    if not plotadas:
        logger.error("nenhuma série disponível para plotar")
        plt.close(fig)
        return

    ax.set_xlabel("Ano", fontsize=12, labelpad=10)
    ax.set_ylabel(f"{ROTULOS['ICSAP']} (%)", fontsize=12, labelpad=10)
    ax.set_title(
        "Evolução das internações evitáveis pela atenção básica",
        fontsize=13, fontweight="bold", pad=14,
    )
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(pivot.index)

    if "Bahia" in pivot.columns:
        for ano, valor in pivot["Bahia"].items():
            ax.annotate(
                f"{valor:.1f}",
                xy=(ano, valor),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center", fontsize=9, color="#c0392b",
            )

    plt.subplots_adjust(bottom=0.24, left=0.10, right=0.95, top=0.92)

    fig.text(
        0.5, 0.015, LEGENDA,
        ha="center", va="bottom",
        fontsize=9, style="italic", color="#555555",
        wrap=True,
        bbox=dict(
            boxstyle="round,pad=0.6",
            facecolor="white",
            edgecolor="#dddddd",
            linewidth=0.8,
            alpha=1.0,
        ),
    )

    destino = PROCESSED_DIR / "evolucao_ba_nordeste.png"
    plt.savefig(destino, dpi=150, facecolor="white")
    logger.info("gráfico salvo em %s", destino)
    plt.close(fig)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    gerar_grafico()