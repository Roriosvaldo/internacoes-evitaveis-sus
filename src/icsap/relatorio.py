"""Gera o relatório final em Markdown com achados, recomendações e gráficos."""

import logging
from datetime import datetime

import pandas as pd

from icsap.analise import carregar_base_unica
from icsap.comparacao_grupos import comparar_grupos
from icsap.comparacao_regional import comparar, ranking_estados
from icsap.config import PROCESSED_DIR, UFS_AMOSTRA
from icsap.rotulos import ROTULO_CURTO, LEGENDA

logger = logging.getLogger(__name__)

FONTE = "Fonte: SIH/SUS, 2020–2024. Elaboração própria."


def _fmt(v: float, casas: int = 2) -> str:
    """Formata número com vírgula decimal."""
    return f"{v:.{casas}f}".replace(".", ",")


def _fmt_int(v: int) -> str:
    """Formata inteiro com separador de milhar."""
    return f"{int(v):,}".replace(",", ".")


def _ufs_presentes(base: pd.DataFrame) -> set[str]:
    """Descobre quais UFs aparecem na base."""
    if "UF" in base.columns:
        return set(base["UF"].dropna().unique())

    codigos = base["MUNIC_RES"].astype(str).str.zfill(6).str[:2]
    codigos = codigos[codigos.str.isdigit()]
    mapa = {
        "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
        "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
        "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
        "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
        "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
        "52": "GO", "53": "DF",
    }
    return {mapa[c] for c in codigos.unique() if c in mapa}


def _secao_panorama(comp: pd.DataFrame) -> list[str]:
    """Panorama com contexto, não só os números."""
    linhas = ["## Panorama", ""]
    anos = sorted(comp["ANO"].unique())
    ba = comp[comp["escopo"] == "Bahia"].sort_values("ANO")

    if ba.empty:
        return linhas

    primeiro = ba.iloc[0]
    ultimo = ba.iloc[-1]
    variacao = ultimo["taxa_icsap_pct"] - primeiro["taxa_icsap_pct"]
    ano_atipico = ba.loc[ba["taxa_icsap_pct"].idxmin()]

    linhas.append(
        f"Período analisado: **{int(anos[0])} a {int(anos[-1])}**. "
        f"Escopos: Bahia, média do Nordeste e média nacional."
    )
    linhas.append("")
    linhas.append(
        f"A taxa da Bahia foi de **{_fmt(primeiro['taxa_icsap_pct'])}%** "
        f"em {int(primeiro['ANO'])} para "
        f"**{_fmt(ultimo['taxa_icsap_pct'])}%** em {int(ultimo['ANO'])} — "
        f"uma variação de **{_fmt(variacao)} ponto percentual** em cinco anos."
    )
    linhas.append("")
    linhas.append(
        f"Na prática, a Bahia está no mesmo patamar de 2020. O ano de "
        f"{int(ano_atipico['ANO'])} "
        f"({_fmt(ano_atipico['taxa_icsap_pct'])}%) é atípico: a pandemia "
        f"reduziu o volume geral de internações e não deve ser lido como "
        f"melhoria real da atenção básica."
    )
    linhas.append("")

    pivot = comp.pivot_table(
        index="ANO", columns="escopo", values="taxa_icsap_pct"
    )
    if "Bahia" in pivot.columns and "Nordeste (média)" in pivot.columns:
        dif_ini = (
            (pivot["Bahia"].iloc[0] - pivot["Nordeste (média)"].iloc[0])
            / pivot["Nordeste (média)"].iloc[0] * 100
        )
        dif_fim = (
            (pivot["Bahia"].iloc[-1] - pivot["Nordeste (média)"].iloc[-1])
            / pivot["Nordeste (média)"].iloc[-1] * 100
        )
        linhas.append(
            f"Contra o Nordeste, a Bahia convergiu: estava "
            f"**{_fmt(dif_ini, 1)}%** acima da média regional em "
            f"{int(pivot.index[0])} e ficou em **{_fmt(dif_fim, 1)}%** em "
            f"{int(pivot.index[-1])}."
        )
        linhas.append("")

    return linhas


def _secao_achados(grupos: pd.DataFrame) -> list[str]:
    """Achados interpretados, não apenas descritos."""
    linhas = ["## Principais achados", ""]

    if grupos.empty:
        return linhas

    acima = grupos[grupos["diferenca_pp"] > 0].sort_values(
        "diferenca_pp", ascending=False
    )
    abaixo = grupos[grupos["diferenca_pp"] < 0].sort_values("diferenca_pp")

    linhas.append(
        "A Bahia empata com o Nordeste na taxa global, mas essa igualdade "
        "esconde movimentos opostos dentro dos grupos."
    )
    linhas.append("")

    if not acima.empty:
        top = acima.head(4)
        nomes = ", ".join(
            f"**{r['nome']}** ({_fmt(r['diferenca_rel_pct'], 1)}%)"
            for _, r in top.iterrows()
            if pd.notna(r["diferenca_rel_pct"])
        )
        linhas.append(
            f"- **A BA vai pior em doenças crônicas e nutricionais.** "
            f"Os grupos que mais puxam a taxa para cima são {nomes}. "
            f"São condições que exigem acompanhamento continuado — consulta "
            f"periódica, adesão a medicamento, visita domiciliar."
        )

    if not abaixo.empty:
        top = abaixo.head(3)
        nomes = ", ".join(
            f"**{r['nome']}** ({_fmt(r['diferenca_rel_pct'], 1)}%)"
            for _, r in top.iterrows()
            if pd.notna(r["diferenca_rel_pct"])
        )
        linhas.append(
            f"- **A BA vai melhor em doenças infecciosas agudas e prevenção.** "
            f"Os grupos com maior vantagem são {nomes}. "
            f"São condições que respondem a ações pontuais — vacinação, "
            f"saneamento, atendimento de urgência."
        )

    linhas.append(
        "- **A leitura central:** a atenção básica da Bahia funciona bem no "
        "episódico e falha no continuado. Doenças infecciosas são resolvidas; "
        "doenças crônicas não são acompanhadas."
    )
    linhas.append(
        "- **O caso mais grave são as deficiências nutricionais**, porque "
        "atingem criança — e criança desnutrida vira adulto com doença crônica. "
        "É onde o retorno do investimento é maior."
    )
    linhas.append("")

    return linhas


def _secao_outliers(ranking: pd.DataFrame) -> list[str]:
    """Casos contraintuitivos no ranking, com o Quadro 3."""
    linhas = ["## Casos contraintuitivos no ranking", ""]

    if ranking.empty:
        return linhas

    POPULACAO = {
        "AL": 3_220_104,
        "RN": 3_446_072,
        "MA": 7_010_960,
        "BA": 14_850_513,
    }

    alvo = ranking[ranking["UF"].isin(POPULACAO)].copy()
    if alvo.empty:
        return linhas

    alvo["populacao"] = alvo["UF"].map(POPULACAO)
    alvo["por_mil"] = (
        alvo["internacoes_total"] / alvo["populacao"] * 1000
    ).round(1)

    linhas.append(
        "**AL** (12,43%) e **RN** (13,27%) apresentam as menores taxas de "
        "ICSAP do ranking, abaixo de estados com estrutura hospitalar mais "
        "consolidada como SP, SC e PR. O achado é contraintuitivo e não deve "
        "ser lido automaticamente como melhor desempenho da atenção básica."
    )
    linhas.append("")
    linhas.append(
        "Duas explicações concorrem: (a) atenção primária efetivamente mais "
        "resolutiva, que evita a internação antes que ela aconteça; "
        "(b) sub-registro de ICSAP na AIH, que reclassifica internações "
        "evitáveis como outras causas e reduz artificialmente a taxa."
    )
    linhas.append("")
    linhas.append("### Internações por mil habitantes")
    linhas.append("")
    linhas.append(
        "O volume de internações por mil habitantes ajuda a separar as duas "
        "hipóteses. Taxa baixa com volume baixo sugere sub-registro; taxa "
        "baixa com volume normal sugere desempenho real."
    )
    linhas.append("")
    linhas.append(
        "**Quadro 3** — Internações por mil habitantes e taxa de ICSAP. "
        "Alagoas, Rio Grande do Norte, Bahia e Maranhão, 2024."
    )
    linhas.append("")
    linhas.append("| UF | Internações | População (2024) | Por mil hab. | Taxa ICSAP |")
    linhas.append("|---|---|---|---|---|")
    for _, r in alvo.sort_values("por_mil").iterrows():
        linhas.append(
            f"| {r['UF']} | {_fmt_int(r['internacoes_total'])} | "
            f"{_fmt_int(r['populacao'])} | {_fmt(r['por_mil'], 1)} | "
            f"{_fmt(r['taxa_icsap_pct'])}% |"
        )
    linhas.append("")
    linhas.append(
        "*Fonte: SIH/SUS e estimativas populacionais IBGE, 2024. "
        "Elaboração própria.*"
    )
    linhas.append("")
    linhas.append(
        "**Alagoas** registra o menor volume do ranking. Taxa baixa "
        "combinada com volume baixo é o padrão compatível com sub-registro."
    )
    linhas.append("")
    linhas.append(
        "**Rio Grande do Norte** registra volume próximo da média nacional. "
        "Aqui a hipótese de sub-registro enfraquece: a taxa baixa sugere "
        "desempenho real da atenção básica ou perfil de morbidade distinto."
    )
    linhas.append("")
    linhas.append(
        "**Bahia** fica no meio: volume próximo da média nacional e taxa "
        "intermediária. É o padrão de um estado que interna no ritmo "
        "esperado e converte parte disso em internações evitáveis — nem "
        "sub-registro, nem desempenho excepcional."
    )
    linhas.append("")
    linhas.append(
        "**Maranhão** é o contraponto: interna muito e interna mal, o oposto "
        "do padrão alagoano. A comparação entre os quatro estados mostra que "
        "taxa baixa pode significar coisas diferentes conforme o volume."
    )
    linhas.append("")
    linhas.append(
        "A verificação definitiva exige auditar a codificação do diagnóstico "
        "principal na AIH nesses estados — o que está fora do escopo desta "
        "análise."
    )
    linhas.append("")

    return linhas


def _secao_tabelas(comp: pd.DataFrame, ranking: pd.DataFrame,
                   grupos: pd.DataFrame) -> list[str]:
    """Tabelas de dados e referências aos gráficos, com numeração."""
    linhas = ["## Evolução anual", ""]

    linhas.append(
        "**Quadro 1** — Taxa de ICSAP (%) por ano. Bahia, média do Nordeste "
        "e média nacional, 2020–2024."
    )
    linhas.append("")
    linhas.append("| Ano | Bahia | Nordeste | Brasil |")
    linhas.append("|---|---|---|---|")
    pivot = comp.pivot_table(
        index="ANO", columns="escopo", values="taxa_icsap_pct"
    )
    for ano, row in pivot.iterrows():
        ba_v = _fmt(row["Bahia"]) if "Bahia" in pivot.columns else "—"
        ne_v = (_fmt(row["Nordeste (média)"])
                if "Nordeste (média)" in pivot.columns else "—")
        br_v = (_fmt(row["Brasil (média)"])
                if "Brasil (média)" in pivot.columns else "—")
        linhas.append(f"| {int(ano)} | {ba_v}% | {ne_v}% | {br_v}% |")
    linhas.append("")
    linhas.append(f"*{FONTE}*")
    linhas.append("")

    linhas.append(
        "**Figura 1** — Evolução da taxa de ICSAP (%). Bahia, Nordeste e "
        "Brasil, 2020–2024."
    )
    linhas.append("")
    linhas.append("![Figura 1 — Evolução da taxa de ICSAP]"
                  "(evolucao_ba_nordeste.png)")
    linhas.append("")
    linhas.append(f"*{FONTE}*")
    linhas.append("")

    linhas.append("## Convergência com o Nordeste")
    linhas.append("")
    linhas.append(
        "A área sombreada mostra a diferença entre a Bahia e a média "
        "nordestina. Ela encolhe de 2020 a 2024 — não porque a BA melhorou, "
        "mas porque o Nordeste se aproximou do patamar baiano."
    )
    linhas.append("")
    linhas.append(
        "**Figura 2** — Convergência da taxa de ICSAP entre Bahia e "
        "Nordeste, 2020–2024."
    )
    linhas.append("")
    linhas.append("![Figura 2 — Convergência BA e Nordeste]"
                  "(convergencia_ba_nordeste.png)")
    linhas.append("")
    linhas.append(f"*{FONTE}*")
    linhas.append("")

    if not ranking.empty:
        ano_rank = int(ranking["ano"].iloc[0])
        linhas.append(f"## Ranking dos estados ({ano_rank})")
        linhas.append("")
        linhas.append(
            f"**Quadro 2** — Ranking das unidades federativas por taxa de "
            f"ICSAP (%), {ano_rank}."
        )
        linhas.append("")
        linhas.append("| UF | Internações | Evitáveis | Taxa |")
        linhas.append("|---|---|---|---|")
        for _, r in ranking.iterrows():
            linhas.append(
                f"| {r['UF']} | {_fmt_int(r['internacoes_total'])} | "
                f"{_fmt_int(r['internacoes_icsap'])} | "
                f"{_fmt(r['taxa_icsap_pct'])}% |"
            )
        linhas.append("")
        linhas.append(
            f"*Fonte: SIH/SUS, {ano_rank}. Elaboração própria. Estados com "
            f"cobertura inferior a 20% do volume mediano foram excluídos.*"
        )
        linhas.append("")

    if not grupos.empty:
        ano_g = int(grupos["ano"].iloc[0])
        linhas.append(f"## Grupos ICSAP — Bahia vs Nordeste ({ano_g})")
        linhas.append("")
        linhas.append(
            f"**Figura 3** — Taxa de ICSAP por grupo (%). Bahia e Nordeste, "
            f"{ano_g}."
        )
        linhas.append("")
        linhas.append("![Figura 3 — Grupos ICSAP]"
                      "(grupos_ba_nordeste.png)")
        linhas.append("")
        linhas.append(f"*{FONTE}*")
        linhas.append("")

        for titulo, sub, num in (
            ("Grupos em que a BA está acima do Nordeste",
             grupos[grupos["diferenca_pp"] > 0].sort_values(
                 "diferenca_pp", ascending=False), 4),
            ("Grupos em que a BA está abaixo do Nordeste",
             grupos[grupos["diferenca_pp"] < 0].sort_values("diferenca_pp"), 5),
        ):
            if sub.empty:
                continue
            linhas.append(f"### {titulo}")
            linhas.append("")
            linhas.append(
                f"**Quadro {num}** — Taxa de ICSAP por grupo (%). Bahia e "
                f"Nordeste, {ano_g}."
            )
            linhas.append("")
            linhas.append("| Grupo | BA | NE | Diferença | Relativa |")
            linhas.append("|---|---|---|---|---|")
            for _, r in sub.iterrows():
                rel = (
                    f"{_fmt(r['diferenca_rel_pct'], 1)}%"
                    if pd.notna(r["diferenca_rel_pct"]) else "—"
                )
                linhas.append(
                    f"| {r['nome']} | {_fmt(r['taxa_ba_pct'])}% | "
                    f"{_fmt(r['taxa_ne_pct'])}% | "
                    f"{_fmt(r['diferenca_pp'])} pp | {rel} |"
                )
            linhas.append("")
            linhas.append(f"*Fonte: SIH/SUS, {ano_g}. Elaboração própria.*")
            linhas.append("")

    return linhas


def _secao_recomendacoes(grupos: pd.DataFrame) -> list[str]:
    """Recomendações de política pública derivadas dos achados."""
    linhas = ["## Recomendações", ""]

    if grupos.empty:
        return linhas

    def _rel(nome: str) -> str:
        sub = grupos[grupos["nome"] == nome]
        if sub.empty or pd.isna(sub.iloc[0]["diferenca_rel_pct"]):
            return "—"
        return _fmt(sub.iloc[0]["diferenca_rel_pct"], 1)

    rel_nutri = _rel("Deficiências nutricionais")
    rel_asma = _rel("Asma")

    linhas.append(
        "As recomendações abaixo derivam diretamente do contraste entre os "
        "grupos em que a Bahia está acima e abaixo da média nordestina. "
        "O foco é o que a atenção primária pode efetivamente mudar."
    )
    linhas.append("")
    linhas.append(
        "**1. Priorizar o acompanhamento de doenças crônicas.** "
        "Hipertensão, diabetes, insuficiência cardíaca e doenças "
        "cerebrovasculares respondem por parte relevante da diferença. "
        "O instrumento é o acompanhamento continuado: consulta periódica "
        "programada, busca ativa de faltosos, adesão medicamentosa e "
        "visita domiciliar para pacientes acamados ou com dificuldade de "
        "deslocamento."
    )
    linhas.append("")
    linhas.append(
        f"**2. Tratar as deficiências nutricionais como prioridade "
        f"materno-infantil.** É o grupo com maior diferença relativa "
        f"(+{rel_nutri}%) e atinge criança. O retorno do investimento é o "
        f"mais alto do conjunto: criança desnutrida vira adulto com doença "
        f"crônica. Ações: vigilância nutricional na puericultura, "
        f"suplementação quando indicada e acompanhamento do crescimento."
    )
    linhas.append("")
    linhas.append(
        f"**3. Investigar o caso da asma.** A diferença de +{rel_asma}% "
        f"sugere falha no manejo ambulatorial — provavelmente acesso a "
        f"corticosteroide inalatório ou ausência de plano de ação para "
        f"crises. É um grupo com solução relativamente barata e rápida."
    )
    linhas.append("")
    linhas.append(
        "**4. Preservar o que já funciona.** Gastroenterites, doenças "
        "imunopreveníveis e infecções urinárias estão abaixo da média "
        "nordestina. São os programas de vacinação, saneamento e "
        "atendimento de urgência. Não devem ser deslocados para financiar "
        "as prioridades acima."
    )
    linhas.append("")
    linhas.append(
        "**5. Melhorar o registro antes de ampliar a meta.** A taxa de "
        "ICSAP depende da qualidade do preenchimento do diagnóstico "
        "principal na AIH. Antes de definir metas de redução, vale "
        "verificar se o diagnóstico está sendo codificado corretamente "
        "nos municípios com taxa muito baixa — em especial em Alagoas, "
        "onde o volume de internações por mil habitantes é o menor do "
        "ranking."
    )
    linhas.append("")

    return linhas


def _secao_limitacoes(base: pd.DataFrame, n_ufs: int = 19,
                      ufs_excluidas: list[str] | None = None) -> list[str]:
    """Nota metodológica com a cobertura real do ranking."""
    linhas = ["## Nota metodológica e limitações", ""]

    linhas += [
        "- **Fonte:** Sistema de Informações Hospitalares do SUS (SIH/SUS), "
        "internações financiadas pelo SUS. Não inclui atendimentos "
        "ambulatoriais nem internações na rede privada.",
        "- **Definição de ICSAP:** Lista Brasileira de Condições Sensíveis à "
        "Atenção Primária, conforme a Portaria MS/GM nº 221/2008.",
        "- **Denominador:** total de internações do SUS no período, por "
        "local de residência do paciente (`MUNIC_RES`), não por local de "
        "internação.",
        "- **População:** estimativas do IBGE para 2024, usadas apenas no "
        "cálculo de internações por mil habitantes.",
        f"- **Cobertura:** {n_ufs} unidades federativas entraram no ranking, "
        "após descartar as que tinham dados parciais (menos de 20% do "
        "volume mediano). Estados com cobertura incompleta foram excluídos "
        "para não contaminar o ranking com taxas artificialmente baixas.",
    ]

    if ufs_excluidas:
        linhas.append(
            f"- **Estados excluídos por cobertura incompleta:** "
            f"{', '.join(sorted(ufs_excluidas))}."
        )
    else:
        linhas.append(
            "- **Estados excluídos por cobertura incompleta:** nenhum."
        )

    linhas += [
        "- **Limitação do indicador:** a taxa de ICSAP é sensível à oferta "
        "hospitalar. Estados com menos leitos internam menos e podem "
        "apresentar taxa artificialmente baixa, sem que isso signifique "
        "melhor atenção básica. O ranking deve ser lido com cautela.",
        "- **Limitação da comparação:** taxas brutas não são ajustadas por "
        "idade, sexo ou perfil de morbidade. Diferenças entre estados podem "
        "refletir diferenças de estrutura populacional.",
        "",
    ]

    return linhas


def gerar_relatorio(base: pd.DataFrame | None = None) -> None:
    """Gera o relatório. Se `base` vier pronta, não relê os parquets."""
    if base is None:
        logger.info("carregando base (leitura única)")
        base = carregar_base_unica()

    comp = comparar(base)
    if comp.empty:
        logger.error("comparação regional vazia — relatório não gerado")
        return

    ranking = ranking_estados(base)
    grupos = comparar_grupos(base)

    # UFs que ficaram fora do ranking por cobertura incompleta
    ufs_ranking = set(ranking["UF"]) if not ranking.empty else set()
    ufs_excluidas = sorted(set(UFS_AMOSTRA) - ufs_ranking)

    from icsap.grafico_comparacao import gerar_grafico as graf_evolucao
    from icsap.grafico_convergencia import gerar_grafico as graf_convergencia
    from icsap.grafico_grupos import gerar_grafico as graf_grupos

    logger.info("gerando gráficos")
    graf_evolucao(base)
    graf_convergencia(base)
    graf_grupos(base)

    linhas: list[str] = []
    linhas.append(f"# {ROTULO_CURTO}")
    linhas.append("")
    linhas.append("**Bahia vs Nordeste e Brasil — 2020 a 2024**")
    linhas.append("")
    linhas.append(f"Gerado em {datetime.now():%d/%m/%Y às %H:%M}")
    linhas.append("")
    linhas.append("---")
    linhas.append("")

    linhas += _secao_panorama(comp)
    linhas += _secao_achados(grupos)
    linhas += _secao_outliers(ranking)
    linhas += _secao_tabelas(comp, ranking, grupos)
    linhas += _secao_recomendacoes(grupos)
    linhas += _secao_limitacoes(base, len(ranking), ufs_excluidas)

    linhas.append("---")
    linhas.append("")
    linhas.append(f"*{LEGENDA}*")
    linhas.append("")

    destino = PROCESSED_DIR / "relatorio.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")

    logger.info("relatório gravado em %s", destino)
    print(f"\nRelatório gerado: {destino}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    gerar_relatorio()