"""Configuração central do projeto internacoes-evitaveis-sus."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Sobe de src/icsap/ até a raiz do projeto e carrega o .env de lá
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_PROJETO / ".env")

# Raiz dos dados — definida no .env, com fallback para ./data
DATA_DIR = Path(os.getenv("ICSAP_DATA_DIR", "./data")).resolve()

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

for _d in (RAW_DIR, INTERIM_DIR, PROCESSED_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --- Parâmetros do estudo ---
UF = os.getenv("ICSAP_UF", "BA")
ANOS = [int(a) for a in os.getenv("ICSAP_ANOS", "2020,2021,2022,2023,2024").split(",")]

# --- FTP do DATASUS ---
FTP_HOST = "ftp.datasus.gov.br"
FTP_BASE = "/dissemin/publicos/SIHSUS/200801_/Dados"
FTP_TIMEOUT = 60

# --- Estados do Nordeste (sigla UF do SIH) ---
UFS_NORDESTE = ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"]

# --- Estados de maior volume, usados como amostra complementar ---
UFS_TOP_VOLUME = ["SP", "MG", "RJ", "RS", "PR", "GO", "AM", "PA", "SC", "ES"]

# --- Amostra completa: top volume + Nordeste ---
UFS_AMOSTRA = sorted(set(UFS_TOP_VOLUME) | set(UFS_NORDESTE))

__all__ = [
    "RAIZ_PROJETO", "DATA_DIR", "RAW_DIR", "INTERIM_DIR", "PROCESSED_DIR",
    "UF", "ANOS", "FTP_HOST", "FTP_BASE", "FTP_TIMEOUT",
    "UFS_NORDESTE", "UFS_TOP_VOLUME", "UFS_AMOSTRA",
]