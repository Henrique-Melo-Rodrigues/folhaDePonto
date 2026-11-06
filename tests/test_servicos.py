"""Serviços de aplicação (WP5): os casos de uso como as telas os chamam, sem Flet."""

from datetime import date, datetime, timedelta

import pytest

from folha_ponto.dados import Origem, Repositorio
from folha_ponto.dominio import ErroDeValidacao, Marcacao, Natureza, Status, TipoDia, TipoPendencia
from folha_ponto.ui.servicos import Servicos, aviso_do_dia, escrever_duracao, ler_data

COMPLETO = {"entrada": "07:45", "saida_almoco": "12:00", "volta_almoco": "13:00", "saida": "14:45"}


class Relogio:
    def __init__(self, agora):
        self.agora = agora

    def __call__(self):
        return self.agora


@pytest.fixture
def relogio():
    return Relogio(datetime(2026, 4, 22, 7, 46, 30))  # quarta depois de Tiradentes


@pytest.fixture
def app(relogio):
    with Repositorio(":memory:") as repo:
        yield Servicos(repo, relogio)


# ---- UC01 ---------------------------------------------------------------------
def test_bater_ponto_cria_o_dia_e_avanca_a_proxima_marcacao(app, relogio):
    painel = app.painel_de_hoje()
    assert painel.lancamento is None and painel.proxima is Marcacao.ENTRADA

    lancamento, marcacao = app.bater_ponto()
    assert marcacao is Marcacao.ENTRADA and lancamento.tipo is TipoDia.TRABALHO
    assert lancamento.marcacoes.entrada.strftime("%H:%M") == "07:46"  # arredonda ao minuto

    relogio.agora = relogio.agora.replace(hour=12, minute=1)
    assert app.bater_ponto()[1] is Marcacao.SAIDA_ALMOCO
    assert app.painel_de_hoje().proxima is Marcacao.VOLTA_ALMOCO


def test_dia_cheio_nao_oferece_botao(app, relogio):
    """UC01 E2."""
    for hora in (7, 9, 11, 13, 15, 17):
        relogio.agora = relogio.agora.replace(hour=hora)
        app.bater_ponto()
    assert app.painel_de_hoje().proxima is None
    with pytest.raises(ErroDeValidacao):
        app.bater_ponto()


def test_ajustar_marcacao_valida_a_ordem(app):
    """UC01 3' e E1 (RN02)."""
    app.ajustar_marcacao(Marcacao.ENTRADA, "07:45")
    with pytest.raises(ErroDeValidacao) as erro:
        app.ajustar_marcacao(Marcacao.SAIDA_ALMOCO, "07:00")
    assert erro.value.campo is Marcacao.SAIDA_ALMOCO
    assert app.painel_de_hoje().marcacoes.saida_almoco is None  # nada gravado


def test_painel_mostra_o_aviso_do_feriado(app, relogio):
    relogio.agora = datetime(2026, 4, 21, 9, 0)
    assert app.painel_de_hoje().aviso == "Feriado: Tiradentes"
    lancamento, _ = app.bater_ponto()
    assert lancamento.tipo is TipoDia.FERIADO  # RN06; as horas viram saldo


def test_bater_ponto_numa_emenda_candidata_descarta_a_emenda(app, relogio):
    relogio.agora = datetime(2026, 4, 20, 7, 45)
    assert app.painel_de_hoje().aviso == "Possível emenda: Tiradentes (terça, 21/04)"
    lancamento, _ = app.bater_ponto()
    assert lancamento.tipo is TipoDia.TRABALHO
    assert app.especial(date(2026, 4, 20)) is None


# ---- UC02, UC03, UC04 ---------------------------------------------------------
def test_formulario_novo_vem_com_o_tipo_sugerido(app):
    form = app.formulario_do_dia(date(2026, 4, 25))  # sábado
    assert (form.tipo, form.existe, form.observacao) == (TipoDia.FOLGA, False, "")
    emenda = app.formulario_do_dia(date(2026, 4, 20))
    assert (emenda.tipo, emenda.observacao) == (TipoDia.FOLGA, "Emenda")
    assert emenda.aviso.startswith("Possível emenda")


def test_salvar_e_reabrir_o_dia(app):
    app.salvar_dia(date(2026, 4, 22), TipoDia.TRABALHO, {**COMPLETO, "entrada_extra": "18:00"}, " obs ")
    form = app.formulario_do_dia(date(2026, 4, 22))
    assert form.existe and form.textos["entrada"] == "07:45" and form.textos["saida_extra"] == ""
    assert form.observacao == "obs"


def test_salvar_dia_invalido_nao_grava(app):
    with pytest.raises(ErroDeValidacao) as erro:
        app.salvar_dia(date(2026, 4, 22), "trabalho", {"entrada": "7:45"})
    assert erro.value.campo is Marcacao.ENTRADA
    assert not app.formulario_do_dia(date(2026, 4, 22)).existe


def test_jornada_padrao_preenche_manha_e_tarde(app):
    assert app.jornada_padrao() == {**COMPLETO, "entrada_extra": "", "saida_extra": ""}


def test_salvar_folga_na_emenda_confirma_e_trabalho_descarta(app):
    """UC03 passo 3."""
    app.salvar_dia(date(2026, 4, 20), TipoDia.FOLGA, {}, "Emenda")
    assert app.especial(date(2026, 4, 20)).natureza is Natureza.EMENDA
    app.salvar_dia(date(2026, 6, 5), TipoDia.TRABALHO, COMPLETO)
    assert app.especial(date(2026, 6, 5)) is None
    assert app.recalcular_calendario() == []
    assert app.especial(date(2026, 4, 20)).natureza is Natureza.EMENDA
    assert app.especial(date(2026, 6, 5)) is None


def test_excluir_mantem_o_feriado(app):
    app.salvar_dia(date(2026, 4, 21), TipoDia.FERIADO, {})
    assert app.excluir_dia(date(2026, 4, 21))
    assert not app.excluir_dia(date(2026, 4, 21))
    assert app.formulario_do_dia(date(2026, 4, 21)).aviso == "Feriado: Tiradentes"


# ---- UC05, UC07, UC08 ---------------------------------------------------------
def test_mes_prepara_o_ano_e_usa_a_jornada_das_preferencias(app):
    app.salvar_dia(date(2026, 4, 22), TipoDia.TRABALHO, COMPLETO)
    abril = app.mes(2026, 4)
    assert app.repo.anos_com_calendario() == {2026}
    resumo = abril.resumo(hoje=date(2026, 4, 22))
    assert resumo.dias_lancados == 1 and resumo.horas == timedelta(hours=6) and resumo.saldo == timedelta()
    pendencias = {p.data: p.tipo for p in abril.pendencias(date(2026, 4, 22))}
    assert pendencias[date(2026, 4, 20)] is TipoPendencia.EMENDA_A_CONFIRMAR
    assert abril.lancamentos[date(2026, 4, 22)].status is Status.COMPLETO


# ---- UC10, UC11 ---------------------------------------------------------------
def test_cadastrar_data_manual_pelo_texto(app):
    app.mes(2026, 3)
    d = app.cadastrar_data("12/03/2026", "Feriado municipal de teste", "feriado", recorrente=True)
    assert d.origem is Origem.MANUAL and d.recorrente
    assert [x.nome for x in app.datas_manuais(2026)] == ["Feriado municipal de teste"]
    assert app.especial(date(2026, 3, 13)).natureza is Natureza.EMENDA_SUGERIDA
    assert app.remover_data(date(2026, 3, 12), "Feriado municipal de teste")
    assert app.datas_manuais(2026) == []


def test_ocultar_data_da_lib(app):
    datas = {(d.data, d.nome): d for d in app.datas_do_ano(2026)}
    assert (date(2026, 10, 28), "Dia do Servidor Público") in datas
    assert app.ocultar_data(date(2026, 10, 28), "Dia do Servidor Público")
    assert app.especial(date(2026, 10, 28)) is None


def test_trocar_uf_recalcula_e_avisa(app):
    app.mes(2026, 7)
    jornada = {"entrada": "08:00", "saida_almoco": "12:00", "volta_almoco": "13:00", "saida": "17:00"}
    avisos = app.salvar_preferencias(uf="xx", municipio=" Cubatão ", jornada=jornada,
                                     facultativo_e_folga=True, tema="escuro")
    assert avisos and "XX" in avisos[0]
    assert app.especial(date(2026, 7, 9)) is None  # some o feriado estadual de SP
    prefs = app.repo.preferencias()
    assert (prefs.uf, prefs.municipio, prefs.tema) == ("XX", "Cubatão", "escuro")
    assert prefs.jornada.duracao == timedelta(hours=8)

    assert app.salvar_preferencias(uf="SP", municipio="Cubatão", jornada=jornada,
                                   facultativo_e_folga=True, tema="claro") == []
    assert app.especial(date(2026, 7, 9)).nome == "Revolução Constitucionalista"


def test_preferencias_validam_a_jornada(app):
    with pytest.raises(ErroDeValidacao):
        app.salvar_preferencias(uf="SP", municipio="", jornada={"entrada": "08:00"},
                                facultativo_e_folga=True, tema="claro")
    with pytest.raises(ErroDeValidacao):
        app.salvar_preferencias(uf="SP", municipio="", facultativo_e_folga=True, tema="claro",
                                jornada={"entrada": "13:00", "saida_almoco": "12:00",
                                         "volta_almoco": "13:30", "saida": "17:00"})


def test_aviso_da_uf_invalida_sai_uma_vez(relogio):
    with Repositorio(":memory:") as repo:
        from folha_ponto.dominio.preferencias import Preferencias
        repo.salvar_preferencias(Preferencias(uf="XX"))
        app = Servicos(repo, relogio)
        app.mes(2026, 4)
        assert len(app.tirar_avisos()) == 1 and app.tirar_avisos() == []


# ---- formatação ---------------------------------------------------------------
def test_formatos():
    assert ler_data("05/11/2026") == ler_data("2026-11-05") == date(2026, 11, 5)
    with pytest.raises(ErroDeValidacao):
        ler_data("31/02/2026")
    assert escrever_duracao(timedelta(hours=6, minutes=5)) == "6h05"
    assert escrever_duracao(timedelta(minutes=-30)) == "−0h30"
    assert escrever_duracao(None) == ""
    assert aviso_do_dia(None) == ""
