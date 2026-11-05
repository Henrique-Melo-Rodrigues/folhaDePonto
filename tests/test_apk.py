"""Configuração do APK (WP7): o que o `flet build apk` lê do pyproject.toml.

O build em si roda no CI (precisa de Flutter e Android SDK); aqui ficam as
garantias baratas que não podem regredir.
"""

import ast
import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PYPROJECT = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
FLET = PYPROJECT["tool"]["flet"]


def test_apk_nao_pede_internet():
    """RNF01: o flet build põe INTERNET por padrão; o projeto precisa tirá-la explicitamente."""
    assert FLET["android"]["permission"]["android.permission.INTERNET"] is False


def test_ponto_de_entrada_do_apk():
    app = RAIZ / FLET["app"]["path"]
    entrada = app / f"{FLET['app']['module']}.py"
    assert entrada.exists()
    assert (app / "folha_ponto" / "__init__.py").exists()  # o pacote vai junto com o main.py
    arvore = ast.parse(entrada.read_text(encoding="utf-8"))
    importa = {(n.module, a.name) for n in ast.walk(arvore) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert ("folha_ponto.ui.app", "main") in importa
    chamadas = [n for n in ast.walk(arvore) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "run"]
    assert len(chamadas) == 1 and chamadas[0].args[0].id == "main"


def test_dependencias_do_apk_sao_so_as_de_execucao():
    """O APK instala [project].dependencies. Ferramentas de PC ficam no grupo dev."""
    nomes = {d.split(">")[0].split("=")[0].split("<")[0].strip() for d in PYPROJECT["project"]["dependencies"]}
    assert nomes == {"flet", "holidays"}
    dev = " ".join(PYPROJECT["dependency-groups"]["dev"])
    assert "flet-web" in dev and "flet-desktop" in dev and "pytest" in dev


def test_app_so_importa_o_que_o_apk_instala():
    """Todo import de terceiros do pacote precisa estar em [project].dependencies."""
    permitidos = {"flet", "holidays", "folha_ponto"} | set(sys.stdlib_module_names)
    pacote = RAIZ / "src" / "folha_ponto"
    for arquivo in [*pacote.rglob("*.py"), RAIZ / "src" / "main.py"]:
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Import):
                nomes = [a.name.split(".")[0] for a in no.names]
            elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
                nomes = [no.module.split(".")[0]]
            else:
                continue
            assert set(nomes) <= permitidos, f"{arquivo.relative_to(RAIZ)}: {nomes}"
