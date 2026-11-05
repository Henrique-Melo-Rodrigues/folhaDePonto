"""RNF01: o app é 100% offline. Nenhum módulo do pacote pode importar rede.

Guarda estrutural desde o primeiro commit da v2 (substitui o
no_network_offline_test.dart do app Flutter).
"""

import ast
from pathlib import Path

import folha_ponto

PACOTE = Path(folha_ponto.__file__).parent
MODULOS_DE_REDE = {
    "socket", "ssl", "http", "urllib", "ftplib", "smtplib", "imaplib", "poplib",
    "xmlrpc", "requests", "httpx", "aiohttp", "urllib3", "websockets",
}


def _imports(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(alias.name.split(".")[0] for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            nomes.add(no.module.split(".")[0])
    return nomes


def test_nenhum_modulo_importa_rede():
    infratores = {
        f"{arquivo.relative_to(PACOTE)}: {sorted(_imports(arquivo) & MODULOS_DE_REDE)}"
        for arquivo in PACOTE.rglob("*.py")
        if _imports(arquivo) & MODULOS_DE_REDE
    }
    assert not infratores, f"o app é offline (RNF01); remova: {infratores}"


def test_guarda_detecta_import_de_rede(tmp_path):
    falso = tmp_path / "x.py"
    falso.write_text("import urllib.request\nfrom http import client\n", encoding="utf-8")
    assert _imports(falso) >= {"urllib", "http"}
