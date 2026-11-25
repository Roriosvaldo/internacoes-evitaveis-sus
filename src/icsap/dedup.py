"""Remove a duplicação do relatorio.py mantendo a primeira cópia."""

from pathlib import Path

ARQUIVO = Path("src/icsap/relatorio.py")
BACKUP = ARQUIVO.with_suffix(".py.bak")

texto = ARQUIVO.read_text(encoding="utf-8")
linhas = texto.splitlines()

# encontra todas as definições de função de nível superior
definicoes = []
for i, linha in enumerate(linhas):
    if linha.startswith("def ") and "(" in linha:
        nome = linha[4:].split("(")[0].strip()
        definicoes.append((i, nome))

# detecta o ponto onde a primeira função reaparece
primeira = definicoes[0][1] if definicoes else None
corte = None

for i, nome in definicoes[1:]:
    if nome == primeira:
        corte = i
        break

if corte is None:
    print("nenhuma duplicação detectada")
else:
    BACKUP.write_text(texto, encoding="utf-8")
    novo = "\n".join(linhas[:corte]).rstrip() + "\n"
    ARQUIVO.write_text(novo, encoding="utf-8")
    print(f"backup salvo em {BACKUP}")
    print(f"relatorio.py: {len(linhas)} -> {corte} linhas")