"""Download dos arquivos DBC do SIH/SUS via FTP do DATASUS."""

import ftplib
import logging
from pathlib import Path

from icsap.config import (
    ANOS, FTP_BASE, FTP_HOST, FTP_TIMEOUT, RAW_DIR, UFS_AMOSTRA,
)

logger = logging.getLogger(__name__)

MESES = [f"{m:02d}" for m in range(1, 13)]


def nome_arquivo(uf: str, ano: int, mes: str) -> str:
    """Monta o nome do DBC: RD + UF + AA + MM + .dbc"""
    return f"RD{uf}{str(ano)[2:]}{mes}.dbc"


def caminho_local(uf: str, ano: int, mes: str) -> Path:
    """Caminho de destino no disco, dentro de raw/."""
    return RAW_DIR / nome_arquivo(uf, ano, mes)


def _conectar() -> ftplib.FTP:
    """Abre conexão com o FTP do DATASUS."""
    logger.info("conectando a %s", FTP_HOST)
    ftp = ftplib.FTP(FTP_HOST, timeout=FTP_TIMEOUT)
    ftp.login()
    ftp.cwd(FTP_BASE)
    return ftp


def baixar_arquivo(ftp: ftplib.FTP, uf: str, ano: int, mes: str) -> bool:
    """Baixa um único DBC. Retorna True se baixou, False se já existia."""
    destino = caminho_local(uf, ano, mes)

    if destino.exists() and destino.stat().st_size > 0:
        logger.debug("já existe, pulando: %s", destino.name)
        return False

    nome = nome_arquivo(uf, ano, mes)

    try:
        with open(destino, "wb") as f:
            ftp.retrbinary(f"RETR {nome}", f.write)
    except ftplib.error_perm as exc:
        logger.warning("não disponível: %s (%s)", nome, exc)
        destino.unlink(missing_ok=True)
        return False

    logger.info("baixado: %s", nome)
    return True


def baixar_tudo(ufs: list[str] | None = None,
                anos: list[int] | None = None) -> None:
    """Baixa todos os DBC de uma lista de UFs e anos."""
    ufs = ufs or UFS_AMOSTRA
    anos = anos or ANOS

    logger.info("=== baixando %d estados ===", len(ufs))
    logger.info("estados: %s", ", ".join(ufs))
    logger.info("anos: %s", anos)

    ftp = _conectar()
    total = 0

    try:
        for uf in ufs:
            for ano in anos:
                logger.info("=== UF %s / ano %d ===", uf, ano)
                for mes in MESES:
                    if baixar_arquivo(ftp, uf, ano, mes):
                        total += 1
    finally:
        ftp.quit()

    logger.info("total baixado: %d arquivos", total)


def verificar_cobertura(uf: str, ano: int) -> int:
    """Conta quantos meses de um UF/ano estão presentes no raw."""
    return sum(
        1 for mes in MESES
        if caminho_local(uf, ano, mes).exists()
        and caminho_local(uf, ano, mes).stat().st_size > 0
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    baixar_tudo()