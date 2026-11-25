"""Gráfico da convergência entre Bahia e Nordeste ao longo dos anos."""

import logging

import matplotlib.pyplot as plt

from icsap.comparacao_regional import comparar
from icsap.config import PROCESSED_DIR
from icsap.rotulos import ROTULOS, LEGENDA

logger = logging.getLogger(__name__)


def gerar_grafico(base=None) -> None:
    """Plota a diferença BA − NE por ano, com área sombreada."""
    comp = comparar(base)

    if comp.empty:
        logger.error("comparação regional vazia — gráfico não gerado")
        return

    pivot = comp.pivot_table(
        index="ANO", columns="escopo", values="taxa_icsap_pct"
    )

    if "Bahia" not in pivot.columns or "Nordeste (média)" not in pivot.columns:
        logger.error("faltam colunas Bahia ou Nordeste — gráfico não gerado")
        return

    anos = pivot.index.astype(int)
    ba = pivot["Bahia"]
    ne = pivot["Nordeste (média)"]
    diferenca = ba - ne

    fig, ax = plt.subplots(figsize=(11, 7.5))

    ax.plot(anos, ba, marker="o", linewidth=2.4, color="#c0392b",
            label="Bahia")
    ax.plot(anos, ne, marker="o", linewidth=2.0, color="#2980b9",
            label="Nordeste (média)")

    # área sombreada entre as duas linhas
    ax.fill_between(anos, ba, ne, color="#95a5a6", alpha=0.25,
                    label="Diferença BA − NE")

    for ano, valor in diferenca.items():
        ax.annotate(
            f"{valor:+.2f} pp",
            xy=(int(ano), (ba.loc[ano] + ne.loc[ano]) / 2),
            ha="center", fontsize=8, color="#555555",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                      edgecolor="none", alpha=0.85),
        )

    ax.set_xlabel("Ano", fontsize=12, labelpad=10)
    ax.set_ylabel(f"{ROTULOS['ICSAP']} (%)", fontsize=12, labelpad=10)
    ax.set_title(
        "Convergência da Bahia com o Nordeste (2020–2024)",
        fontsize=13, fontweight="bold", pad=14,
    )
    ax.legend(fontsize=10, loc="best")
    ax.grid(True, alpha=0.3)
    ax.set_xticks(anos)

    plt.subplots_adjust(bottom=0.24, left=0.10, right=0.95, top=0.92)

    fig.text(
        0.5, 0.015, LEGENDA,
        ha="center", va="bottom",
        fontsize=9, style="italic", color="#555555",
        wrap=True,
        bbox=dict(boxstyle="round,pad=0.6", facecolor="white",
                  edgecolor="#dddddd", linewidth=0.8, alpha=1.0),
    )

    destino = PROCESSED_DIR / "convergencia_ba_nordeste.png"
    plt.savefig(destino, dpi=150, facecolor="white")
    logger.info("gráfico salvo em %s", destino)
    plt.close(fig)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    gerar_grafico()