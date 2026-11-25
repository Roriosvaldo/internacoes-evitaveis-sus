"""Rótulos e legendas para exibição dos resultados."""

ROTULO_CURTO = "Internações evitáveis pela atenção básica"

LEGENDA = (
    "Internações evitáveis pela atenção básica — internações por condições "
    "sensíveis à atenção primária (ICSAP), conforme a Lista Brasileira da "
    "Portaria MS/GM nº 221/2008. São internações que a atenção primária, "
    "quando bem estruturada, tem condições de prevenir ou reduzir."
)

ROTULOS = {
    "ICSAP": ROTULO_CURTO,
    "taxa_icsap_pct": "Taxa de internações evitáveis (%)",
    "ICSAP_GRUPO": "Grupo",
    "ICSAP_NOME": "Grupo de causa",
}


def adicionar_legenda(fig, texto: str = LEGENDA) -> None:
    """Adiciona a legenda explicativa ao rodapé da figura."""
    fig.text(
        0.5, 0.015, texto,
        ha="center", va="bottom",
        fontsize=8, style="italic", color="#555555",
        wrap=True,
        bbox=dict(
            boxstyle="square,pad=0.4",
            facecolor="white",
            edgecolor="none",
            alpha=0.9,
        ),
    )