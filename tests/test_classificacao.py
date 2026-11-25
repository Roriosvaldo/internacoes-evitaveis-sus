"""Testes da classificação ICSAP."""

import pandas as pd
import pytest

from icsap.classificacao_icsap import classificar_dataframe


def test_cid_icsap_conhecido():
    """Um CID da lista ICSAP deve ser classificado como 1."""
    df = pd.DataFrame({"DIAG_PRINC": ["J189"]})  # pneumonia
    resultado = classificar_dataframe(df, coluna="DIAG_PRINC")
    assert resultado["ICSAP"].iloc[0] == 1


def test_cid_nao_icsap():
    """Um CID fora da lista deve ser classificado como 0."""
    df = pd.DataFrame({"DIAG_PRINC": ["S720"]})  # fratura de fêmur
    resultado = classificar_dataframe(df, coluna="DIAG_PRINC")
    assert resultado["ICSAP"].iloc[0] == 0


def test_cid_vazio():
    """CID vazio não deve quebrar a classificação."""
    df = pd.DataFrame({"DIAG_PRINC": [None, ""]})
    resultado = classificar_dataframe(df, coluna="DIAG_PRINC")
    assert resultado["ICSAP"].notna().all()