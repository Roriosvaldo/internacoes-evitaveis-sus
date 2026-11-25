"""Classificação de internações segundo a Lista Brasileira de ICSAP.

Portaria MS/GM nº 221/2008.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

__all__ = [
    "GRUPOS_ICSAP",
    "classificar_codigo",
    "classificar_dataframe",
    "classificar_serie",
]

# Lista Brasileira de ICSAP — Portaria MS/GM nº 221/2008
# chave: prefixo CID-10 (3 ou 4 caracteres) -> (grupo, nome do grupo)
GRUPOS_ICSAP = {
    # 1. Doenças preveníveis por imunização e condições sensíveis
    "A19": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "A33": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "A34": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "A35": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "A36": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "A37": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "A80": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "B05": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "B06": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "B16": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "B18": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "B19": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    "B26": (1, "Doenças preveníveis por imunização e condições sensíveis"),
    # 2. Gastroenterites infecciosas e complicações
    "A00": (2, "Gastroenterites infecciosas e complicações"),
    "A01": (2, "Gastroenterites infecciosas e complicações"),
    "A02": (2, "Gastroenterites infecciosas e complicações"),
    "A03": (2, "Gastroenterites infecciosas e complicações"),
    "A04": (2, "Gastroenterites infecciosas e complicações"),
    "A05": (2, "Gastroenterites infecciosas e complicações"),
    "A06": (2, "Gastroenterites infecciosas e complicações"),
    "A07": (2, "Gastroenterites infecciosas e complicações"),
    "A08": (2, "Gastroenterites infecciosas e complicações"),
    "A09": (2, "Gastroenterites infecciosas e complicações"),
    "E86": (2, "Gastroenterites infecciosas e complicações"),
    # 3. Anemia
    "D50": (3, "Anemia"),
    # 4. Deficiências nutricionais
    "E40": (4, "Deficiências nutricionais"),
    "E41": (4, "Deficiências nutricionais"),
    "E42": (4, "Deficiências nutricionais"),
    "E43": (4, "Deficiências nutricionais"),
    "E44": (4, "Deficiências nutricionais"),
    "E45": (4, "Deficiências nutricionais"),
    "E46": (4, "Deficiências nutricionais"),
    "E50": (4, "Deficiências nutricionais"),
    "E51": (4, "Deficiências nutricionais"),
    "E52": (4, "Deficiências nutricionais"),
    "E53": (4, "Deficiências nutricionais"),
    "E54": (4, "Deficiências nutricionais"),
    "E55": (4, "Deficiências nutricionais"),
    "E56": (4, "Deficiências nutricionais"),
    "E57": (4, "Deficiências nutricionais"),
    "E58": (4, "Deficiências nutricionais"),
    "E59": (4, "Deficiências nutricionais"),
    "E60": (4, "Deficiências nutricionais"),
    "E61": (4, "Deficiências nutricionais"),
    "E62": (4, "Deficiências nutricionais"),
    "E63": (4, "Deficiências nutricionais"),
    "E64": (4, "Deficiências nutricionais"),
    # 5. Infecções de ouvido, nariz e garganta
    "H66": (5, "Infecções de ouvido, nariz e garganta"),
    "J00": (5, "Infecções de ouvido, nariz e garganta"),
    "J01": (5, "Infecções de ouvido, nariz e garganta"),
    "J02": (5, "Infecções de ouvido, nariz e garganta"),
    "J03": (5, "Infecções de ouvido, nariz e garganta"),
    "J06": (5, "Infecções de ouvido, nariz e garganta"),
    "J31": (5, "Infecções de ouvido, nariz e garganta"),
    # 6. Pneumonias bacterianas
    "J13": (6, "Pneumonias bacterianas"),
    "J14": (6, "Pneumonias bacterianas"),
    "J15": (6, "Pneumonias bacterianas"),
    "J16": (6, "Pneumonias bacterianas"),
    "J18": (6, "Pneumonias bacterianas"),
    # 7. Asma
    "J45": (7, "Asma"),
    "J46": (7, "Asma"),
    # 8. Doenças pulmonares
    "J20": (8, "Doenças pulmonares"),
    "J21": (8, "Doenças pulmonares"),
    "J40": (8, "Doenças pulmonares"),
    "J41": (8, "Doenças pulmonares"),
    "J42": (8, "Doenças pulmonares"),
    "J43": (8, "Doenças pulmonares"),
    "J44": (8, "Doenças pulmonares"),
    "J47": (8, "Doenças pulmonares"),
    # 9. Hipertensão
    "I10": (9, "Hipertensão"),
    "I11": (9, "Hipertensão"),
    # 10. Angina
    "I20": (10, "Angina"),
    # 11. Insuficiência cardíaca
    "I50": (11, "Insuficiência cardíaca"),
    "J81": (11, "Insuficiência cardíaca"),
    # 12. Doenças cerebrovasculares
    "I63": (12, "Doenças cerebrovasculares"),
    "I64": (12, "Doenças cerebrovasculares"),
    "I65": (12, "Doenças cerebrovasculares"),
    "I66": (12, "Doenças cerebrovasculares"),
    "I67": (12, "Doenças cerebrovasculares"),
    "I69": (12, "Doenças cerebrovasculares"),
    "G45": (12, "Doenças cerebrovasculares"),
    "G46": (12, "Doenças cerebrovasculares"),
    # 13. Diabetes mellitus
    "E10": (13, "Diabetes mellitus"),
    "E11": (13, "Diabetes mellitus"),
    "E12": (13, "Diabetes mellitus"),
    "E13": (13, "Diabetes mellitus"),
    "E14": (13, "Diabetes mellitus"),
    # 14. Epilepsias
    "G40": (14, "Epilepsias"),
    "G41": (14, "Epilepsias"),
    # 15. Infecção no rim e trato urinário
    "N10": (15, "Infecção no rim e trato urinário"),
    "N11": (15, "Infecção no rim e trato urinário"),
    "N12": (15, "Infecção no rim e trato urinário"),
    "N30": (15, "Infecção no rim e trato urinário"),
    "N34": (15, "Infecção no rim e trato urinário"),
    "N39": (15, "Infecção no rim e trato urinário"),
    # 16. Infecção da pele e tecido subcutâneo
    "A46": (16, "Infecção da pele e tecido subcutâneo"),
    "L01": (16, "Infecção da pele e tecido subcutâneo"),
    "L02": (16, "Infecção da pele e tecido subcutâneo"),
    "L03": (16, "Infecção da pele e tecido subcutâneo"),
    "L04": (16, "Infecção da pele e tecido subcutâneo"),
    "L08": (16, "Infecção da pele e tecido subcutâneo"),
    # 17. Doença inflamatória dos órgãos pélvicos femininos
    "N70": (17, "Doença inflamatória dos órgãos pélvicos femininos"),
    "N71": (17, "Doença inflamatória dos órgãos pélvicos femininos"),
    "N72": (17, "Doença inflamatória dos órgãos pélvicos femininos"),
    "N73": (17, "Doença inflamatória dos órgãos pélvicos femininos"),
    "N75": (17, "Doença inflamatória dos órgãos pélvicos femininos"),
    "N76": (17, "Doença inflamatória dos órgãos pélvicos femininos"),
    # 18. Úlcera gastrointestinal
    "K25": (18, "Úlcera gastrointestinal"),
    "K26": (18, "Úlcera gastrointestinal"),
    "K27": (18, "Úlcera gastrointestinal"),
    "K28": (18, "Úlcera gastrointestinal"),
    # 19. Doenças relacionadas ao pré-natal e parto
    "O23": (19, "Doenças relacionadas ao pré-natal e parto"),
    "B20": (1, "Doenças preveníveis por imunização e condições sensíveis"),
}


def classificar_codigo(codigo: str) -> tuple[int | None, str | None, int]:
    """Classifica um único código CID-10.

    Aceita 3 ou 4 caracteres. Tenta a chave de 4 primeiro e cai
    para a de 3 quando necessário.
    """
    if not codigo or not isinstance(codigo, str):
        return None, None, 0

    chave = codigo.strip().upper()

    if not chave:
        return None, None, 0

    # tenta 4 caracteres, depois 3
    for tamanho in (4, 3):
        prefixo = chave[:tamanho]
        if prefixo in GRUPOS_ICSAP:
            grupo, nome = GRUPOS_ICSAP[prefixo]
            return grupo, nome, 1

    return None, None, 0


def classificar_serie(diag: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Classifica uma série de códigos CID-10 em blocos.

    Evita o MemoryError em bases grandes: processa em partes e
    devolve três séries alinhadas ao índice original.
    """
    TAMANHO_BLOCO = 5_000_000
    n = len(diag)

    grupos = pd.Series(index=diag.index, dtype="object")
    nomes = pd.Series(index=diag.index, dtype="object")
    flags = pd.Series(0, index=diag.index, dtype="int8")

    for inicio in range(0, n, TAMANHO_BLOCO):
        fim = min(inicio + TAMANHO_BLOCO, n)
        bloco = diag.iloc[inicio:fim]

        g_bloco = []
        n_bloco = []
        f_bloco = []

        for codigo in bloco:
            g, nm, f = classificar_codigo(codigo)
            g_bloco.append(g)
            n_bloco.append(nm)
            f_bloco.append(f)

        idx = bloco.index
        grupos.loc[idx] = g_bloco
        nomes.loc[idx] = n_bloco
        flags.loc[idx] = pd.array(f_bloco, dtype="int8")

        if (inicio // TAMANHO_BLOCO) % 5 == 0:
            logger.info("classificados %d/%d registros", fim, n)

    return grupos, nomes, flags


def classificar_dataframe(df: pd.DataFrame, coluna: str = "DIAG_PRINC") -> pd.DataFrame:
    """Classifica ICSAP sem copiar a base inteira.

    Evita o MemoryError em bases grandes: em vez de df.copy(),
    adiciona as colunas diretamente e classifica por blocos.
    """
    if coluna not in df.columns:
        raise KeyError(f"coluna {coluna!r} não encontrada no DataFrame")

    logger.info("classificando %d registros", len(df))

    # só limpa espaços e maiúsculas — NUNCA remove letras
    diag = df[coluna].astype(str).str.strip().str.upper()

    grupos, nomes, flags = classificar_serie(diag)

    df["ICSAP_GRUPO"] = grupos
    df["ICSAP_NOME"] = nomes
    df["ICSAP"] = flags

    total = int(flags.sum())
    logger.info(
        "classificação concluída: %d ICSAP de %d internações (%.2f%%)",
        total, len(df), total / len(df) * 100 if len(df) else 0,
    )

    return df