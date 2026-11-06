"""Telas Flet (WP5): montadas sobre uma Page falsa; os botões são acionados de verdade.

Não abre janela: confere que cada aba monta, que os toques chamam o caso de uso
certo e que a camada de UI não fala SQL.
"""

import ast
from datetime import date, datetime
from pathlib import Path

import flet as ft
import pytest

import folha_ponto.ui
from folha_ponto.dados import Repositorio
from folha_ponto.dominio import Marcacao, Natureza, TipoDia
from folha_ponto.ui.app import App
from folha_ponto.ui.servicos import Servicos

COMPLETO = {"entrada": "07:45", "saida_almoco": "12:00", "volta_almoco": "13:00", "saida": "14:45"}


class PaginaFalsa:
    def __init__(self):
        self.controls, self.dialogos, self.atualizacoes = [], [], 0
        self.title = self.navigation_bar = self.theme = self.dark_theme = self.theme_mode = self.bgcolor = None

    def add(self, *controles):
        self.controls.extend(controles)

    def update(self):
        self.atualizacoes += 1

    def show_dialog(self, dialogo):
        self.dialogos.append(dialogo)

    def pop_dialog(self):
        for i in range(len(self.dialogos) - 1, -1, -1):  # o SnackBar não é fechado por pop_dialog
            if isinstance(self.dialogos[i], ft.AlertDialog):
                return self.dialogos.pop(i)

    @property
    def dialogo(self):
        abertos = [d for d in self.dialogos if isinstance(d, ft.AlertDialog)]
        return abertos[-1] if abertos else None

    @property
    def avisos(self):
        return [d.content.value for d in self.dialogos if isinstance(d, ft.SnackBar)]


class Relogio:
    def __init__(self, agora):
        self.agora = agora

    def __call__(self):
        return self.agora


def filhos(c):
    for nome in ("content", "controls", "actions", "title", "subtitle", "leading", "trailing"):
        valor = getattr(c, nome, None)
        if isinstance(valor, list):
            yield from valor
        elif isinstance(valor, ft.Control):
            yield valor


def todos(raiz):
    pilha = [raiz]
    while pilha:
        c = pilha.pop()
        yield c
        pilha.extend(reversed(list(filhos(c))))


def textos(raiz):
    return [c.value for c in todos(raiz) if isinstance(c, ft.Text) and c.value]


def botao(raiz, rotulo):
    for c in todos(raiz):
        if isinstance(c, (ft.Button, ft.TextButton, ft.FilledButton)) and isinstance(c.content, str) \
                and c.content.startswith(rotulo):
            return c
    raise AssertionError(f"botão {rotulo!r} não encontrado; textos: {textos(raiz)}")


def clicar(controle):
    controle.on_click(None)


@pytest.fixture
def relogio():
    return Relogio(datetime(2026, 4, 22, 7, 46))


@pytest.fixture
def pagina():
    return PaginaFalsa()


@pytest.fixture
def app(pagina, relogio):
    with Repositorio(":memory:") as repo:
        yield App(pagina, Servicos(repo, relogio))


def corpo(app):
    return app.corpo.content


# ---- montagem -------------------------------------------------------------------
def test_abre_na_aba_hoje_com_quatro_abas(app, pagina):
    assert len(pagina.navigation_bar.destinations) == 4 and pagina.navigation_bar.selected_index == 0
    assert "Quarta, 22/04/2026" in textos(corpo(app))
    for i, aba in enumerate(("mes", "folha", "ajustes", "hoje")):
        app.ir_para(aba)
        assert corpo(app) is app.telas[aba].raiz and corpo(app).controls
        assert pagina.navigation_bar.selected_index == ("hoje", "mes", "folha", "ajustes").index(aba)


def test_troca_de_aba_pela_barra(app, pagina):
    pagina.navigation_bar.selected_index = 2
    pagina.navigation_bar.on_change(type("E", (), {"control": pagina.navigation_bar})())
    assert app.aba == "folha"


# ---- Hoje (UC01) ----------------------------------------------------------------
def test_um_toque_registra_a_entrada(app, pagina, relogio):
    clicar(botao(corpo(app), "Registrar Entrada"))
    assert app.servicos.repo.obter(date(2026, 4, 22)).marcacoes.entrada.strftime("%H:%M") == "07:46"
    assert "07:46" in textos(corpo(app))
    assert pagina.avisos[-1] == "Entrada registrada às 07:46."
    botao(corpo(app), "Registrar Saída almoço")


def test_ajustar_marcacao_com_hora_fora_de_ordem_mostra_o_erro(app, pagina):
    app.servicos.ajustar_marcacao(Marcacao.ENTRADA, "08:00")
    app.ir_para("hoje")
    tela = app.telas["hoje"]
    tela.pedir_horario(Marcacao.SAIDA_ALMOCO, "")
    campo = next(c for c in todos(pagina.dialogo) if isinstance(c, ft.TextField))
    campo.value = "07:00"
    clicar(botao(pagina.dialogo, "Salvar"))
    assert campo.error and pagina.dialogo is not None  # continua aberto
    campo.value = "12:00"
    clicar(botao(pagina.dialogo, "Salvar"))
    assert pagina.dialogo is None
    assert app.servicos.repo.obter(date(2026, 4, 22)).marcacoes.saida_almoco.hour == 12


def test_feriado_aparece_na_aba_hoje(pagina, relogio):
    relogio.agora = datetime(2026, 4, 21, 9, 0)
    with Repositorio(":memory:") as repo:
        app = App(pagina, Servicos(repo, relogio))
        assert "Feriado: Tiradentes" in textos(corpo(app))


# ---- formulário do dia (UC02, UC03, UC04) --------------------------------------
def test_formulario_salva_com_jornada_padrao(app, pagina):
    app.abrir_dia(date(2026, 4, 23))
    clicar(botao(pagina.dialogo, "Usar jornada padrão"))
    clicar(botao(pagina.dialogo, "Salvar"))
    salvo = app.servicos.repo.obter(date(2026, 4, 23))
    assert salvo.tipo is TipoDia.TRABALHO and salvo.marcacoes.saida.strftime("%H:%M") == "14:45"
    assert pagina.dialogo is None and pagina.avisos[-1] == "Dia 23/04 salvo."


def test_formulario_invalido_destaca_o_campo(app, pagina):
    app.abrir_dia(date(2026, 4, 23))
    campos = [c for c in todos(pagina.dialogo) if isinstance(c, ft.TextField)]
    entrada = next(c for c in campos if c.label == "Entrada")
    entrada.value = "25:00"
    clicar(botao(pagina.dialogo, "Salvar"))
    assert entrada.error and pagina.dialogo is not None
    assert app.servicos.repo.obter(date(2026, 4, 23)) is None


def test_emenda_vem_como_folga_e_salvar_confirma(app, pagina):
    app.abrir_dia(date(2026, 4, 20))
    dropdown = next(c for c in todos(pagina.dialogo) if isinstance(c, ft.Dropdown))
    assert dropdown.value == "folga"
    assert any(t.startswith("Possível emenda") for t in textos(pagina.dialogo))
    clicar(botao(pagina.dialogo, "Salvar"))
    assert app.servicos.especial(date(2026, 4, 20)).natureza is Natureza.EMENDA


def test_excluir_pede_confirmacao(app, pagina):
    app.servicos.salvar_dia(date(2026, 4, 23), TipoDia.TRABALHO, COMPLETO)
    app.abrir_dia(date(2026, 4, 23))
    clicar(botao(pagina.dialogo, "Excluir"))
    assert "Excluir lançamento?" in textos(pagina.dialogo)
    clicar(botao(pagina.dialogo, "Cancelar"))
    assert app.servicos.repo.obter(date(2026, 4, 23)) is not None

    app.abrir_dia(date(2026, 4, 23))
    clicar(botao(pagina.dialogo, "Excluir"))
    clicar(botao(pagina.dialogo, "Excluir"))
    assert app.servicos.repo.obter(date(2026, 4, 23)) is None


# ---- Mês (UC05, UC07) ----------------------------------------------------------
def test_mes_mostra_grade_resumo_pendencias_e_navega(app, pagina):
    app.servicos.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, COMPLETO)
    app.ir_para("mes")
    t = textos(corpo(app))
    assert "Abril 2026" in t and "Tiradentes" in t and "07:45" in t
    assert any(x.startswith("Pendências: ") for x in t)
    assert any("Emenda a confirmar" in x for x in t)

    pendencia = next(c for c in todos(corpo(app)) if isinstance(c, ft.ListTile))
    clicar(pendencia)
    assert pagina.dialogo is not None
    pagina.pop_dialog()

    proximo = next(c for c in todos(corpo(app)) if isinstance(c, ft.IconButton) and c.tooltip == "Próximo mês")
    clicar(proximo)
    assert (app.ano, app.mes) == (2026, 5) and "Maio 2026" in textos(corpo(app))


def test_mes_atravessa_o_ano_e_prepara_o_calendario(app):
    app.ano, app.mes = 2026, 12
    app.ir_para("mes")
    clicar(next(c for c in todos(corpo(app)) if isinstance(c, ft.IconButton) and c.tooltip == "Próximo mês"))
    assert (app.ano, app.mes) == (2027, 1)
    assert 2027 in app.servicos.repo.anos_com_calendario()


# ---- Folha (UC08) --------------------------------------------------------------
def test_folha_avisa_pendencias_e_lista_todos_os_dias(app, pagina):
    app.ir_para("folha")
    assert any("pendência" in t for t in textos(corpo(app)))
    clicar(botao(corpo(app), "Ver mesmo assim"))
    t = textos(corpo(app))
    assert "01 Q" in t and "30 Q" in t  # abril: 01 a 30 corridos (RN10)
    assert "Feriado — Tiradentes" in t and "Sábado" in t


def test_folha_resolver_volta_ao_mes(app):
    app.ir_para("folha")
    clicar(botao(corpo(app), "Resolver"))
    assert app.aba == "mes"


def test_linha_copiada_e_reinicia_ao_trocar_de_mes(app):
    app.ir_para("folha")
    tela = app.telas["folha"]
    tela.mostrar_mesmo_assim()
    tela.alternar_copiada(3)
    assert tela.copiadas == {3}
    tela.alternar_copiada(3)
    tela.alternar_copiada(4)
    assert tela.copiadas == {4}
    app.mes = 5
    tela.atualizar()
    assert tela.copiadas == set() and not tela.ver_mesmo_assim


# ---- Ajustes (UC10, UC11) ------------------------------------------------------
def test_ajustes_salva_preferencias_e_aplica_o_tema(app, pagina):
    app.ir_para("ajustes")
    tela = app.telas["ajustes"]
    tela.escuro.value = True
    tela.jornada[Marcacao.SAIDA].value = "15:00"
    clicar(botao(corpo(app), "Salvar preferências"))
    assert app.servicos.repo.preferencias().tema == "escuro"
    assert pagina.theme_mode == ft.ThemeMode.DARK
    assert pagina.avisos[-1] == "Preferências salvas."


def test_ajustes_mostra_erro_na_jornada(app):
    app.ir_para("ajustes")
    tela = app.telas["ajustes"]
    tela.jornada[Marcacao.ENTRADA].value = "abc"
    clicar(botao(corpo(app), "Salvar preferências"))
    assert tela.erro.visible and app.servicos.repo.preferencias().jornada.entrada.hour == 7


def test_ajustes_cadastra_remove_e_oculta_datas(app, pagina):
    app.ir_para("ajustes")
    tela = app.telas["ajustes"]
    tela.nova_data.value, tela.novo_nome.value = "12/03/2026", "Feriado municipal de teste"
    clicar(botao(corpo(app), "Adicionar data"))
    assert "12/03 · Feriado municipal de teste" in textos(corpo(app))
    assert "13/03 · Feriado municipal de teste (quinta, 12/03)" in textos(corpo(app))

    tela.remover(next(d for d in app.servicos.datas_manuais(2026)))
    assert "12/03 · Feriado municipal de teste" not in textos(corpo(app))

    servidor = next(d for d in app.servicos.datas_do_ano(2026) if d.nome == "Dia do Servidor Público")
    tela.alternar_oculta(servidor)
    assert app.servicos.especial(date(2026, 10, 28)) is None


def test_ajustes_data_invalida_avisa(app, pagina):
    app.ir_para("ajustes")
    tela = app.telas["ajustes"]
    tela.nova_data.value, tela.novo_nome.value = "31/02/2026", "x"
    clicar(botao(corpo(app), "Adicionar data"))
    assert pagina.avisos[-1] == "Use a data no formato DD/MM/AAAA."


# ---- camadas -------------------------------------------------------------------
PACOTE = Path(folha_ponto.ui.__file__).parent.parent


def _modulos_importados(pasta):
    for arquivo in (PACOTE / pasta).rglob("*.py"):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Import):
                yield arquivo, [a.name.split(".")[0] for a in no.names]
            elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
                yield arquivo, [no.module.split(".")[0]]


def test_ui_nao_fala_sql():
    """CLAUDE.md: só dados/ usa sqlite3."""
    for arquivo, nomes in _modulos_importados("ui"):
        assert "sqlite3" not in nomes, arquivo


@pytest.mark.parametrize("pasta", ["dominio", "calendario", "dados"])
def test_so_a_ui_importa_flet(pasta):
    for arquivo, nomes in _modulos_importados(pasta):
        assert "flet" not in nomes, arquivo


# ---- WP6: exportar a folha (UC08 2') e backup (UC09) ------------------------------
class Aparelho:
    """Grava o que as telas pediram ao aparelho (compartilhar, salvar, copiar, escolher)."""

    def __init__(self, app, arquivo_escolhido=None):
        self.chamadas = []
        app.compartilhar_texto = lambda texto, assunto: self.chamadas.append(("texto", assunto, texto))
        app.compartilhar_arquivo = lambda nome, dados, mime: self.chamadas.append(("arquivo", nome, dados, mime))
        app.salvar_arquivo = lambda nome, dados: self.chamadas.append(("salvar", nome, dados))
        app.copiar = lambda texto: self.chamadas.append(("copiar", texto))
        app.escolher_arquivo = lambda ao_escolher, extensoes: ao_escolher(arquivo_escolhido)


def test_folha_compartilha_texto_csv_e_copia(app):
    app.servicos.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, COMPLETO)
    aparelho = Aparelho(app)
    app.ir_para("folha")
    clicar(botao(corpo(app), "Ver mesmo assim"))
    clicar(botao(corpo(app), "Texto"))
    clicar(botao(corpo(app), "CSV"))
    clicar(botao(corpo(app), "Copiar"))
    (_, assunto, texto), (_, nome, dados, mime), (_, copiado) = aparelho.chamadas
    assert assunto == "folha-2026-04" and "01 Qua  07:45 12:00   13:00 14:45" in texto
    assert (nome, mime) == ("folha-2026-04.csv", "text/csv") and dados.startswith(b"\xef\xbb\xbfdia;")
    assert copiado == texto


def test_fazer_backup_compartilha_ou_salva(app, pagina):
    app.servicos.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, COMPLETO)
    aparelho = Aparelho(app)
    app.ir_para("ajustes")
    clicar(botao(corpo(app), "Fazer backup"))
    clicar(botao(pagina.dialogo, "Compartilhar"))
    assert pagina.dialogo is None
    clicar(botao(corpo(app), "Fazer backup"))
    clicar(botao(pagina.dialogo, "Salvar arquivo"))
    (tipo1, nome1, dados1, mime), (tipo2, nome2, dados2) = aparelho.chamadas
    assert (tipo1, tipo2, mime) == ("arquivo", "salvar", "application/json")
    assert nome1 == nome2 == "backup-2026-04-22.json" and dados1 == dados2
    assert b'"2026-04-01"' in dados1


def test_restaurar_pelo_botao_mostra_resumo_e_mescla(app, pagina, relogio):
    with Repositorio(":memory:") as outro_repo:
        outro = Servicos(outro_repo, relogio)
        outro.salvar_dia(date(2026, 4, 2), TipoDia.TRABALHO, COMPLETO, "do backup")
        _, conteudo = outro.gerar_backup()
    app.servicos.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, COMPLETO, "do aparelho")
    Aparelho(app, conteudo.encode("utf-8"))
    app.ir_para("ajustes")
    clicar(botao(corpo(app), "Restaurar"))
    assert any("1 dia(s) lançado(s)" in t for t in textos(pagina.dialogo))
    clicar(botao(pagina.dialogo, "Mesclar"))
    assert pagina.dialogo is None
    assert {l.observacao for l in app.servicos.repo.listar_mes(2026, 4)} == {"do aparelho", "do backup"}
    assert pagina.avisos[-1] == "Backup restaurado: 1 dia(s) importado(s)."


def test_restaurar_substituindo_traz_as_preferencias(app, pagina, relogio):
    with Repositorio(":memory:") as outro_repo:
        outro = Servicos(outro_repo, relogio)
        outro.salvar_preferencias(uf="SP", municipio="Cubatão", jornada=COMPLETO, facultativo_e_folga=True,
                                  tema="escuro")
        _, conteudo = outro.gerar_backup()
    app.servicos.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, COMPLETO)
    Aparelho(app, conteudo.encode("utf-8"))
    app.ir_para("ajustes")
    clicar(botao(corpo(app), "Restaurar"))
    clicar(botao(pagina.dialogo, "Substituir tudo"))
    assert app.servicos.repo.listar_mes(2026, 4) == []
    assert pagina.theme_mode == ft.ThemeMode.DARK and app.telas["ajustes"].escuro.value is True


def test_restaurar_arquivo_invalido_avisa_e_nao_importa(app, pagina):
    app.servicos.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, COMPLETO)
    Aparelho(app, b'{"formato": "outro"}')
    app.ir_para("ajustes")
    clicar(botao(corpo(app), "Restaurar"))
    assert pagina.dialogo is None and pagina.avisos[-1] == "O arquivo não é um backup da Folha de Ponto."
    assert len(app.servicos.repo.listar_mes(2026, 4)) == 1


def test_falha_do_servico_do_aparelho_vira_aviso(app, pagina):
    """Ex.: plataforma sem menu Compartilhar. A tarefa assíncrona não pode morrer calada."""
    import asyncio

    pagina.run_task = lambda tarefa: asyncio.run(tarefa())

    async def quebra():
        raise RuntimeError("sem suporte")

    app._em_segundo_plano(quebra, "Não deu para compartilhar")
    assert pagina.avisos[-1] == "Não deu para compartilhar: sem suporte"
