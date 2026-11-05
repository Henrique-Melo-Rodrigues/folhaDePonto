"""UC01 (bater ponto), RN06 (tipo sugerido), RN07 (dia útil), UC07 (pendências), UC08/RN10 (folha).

Datas reais de 2026: 03/04 sexta-feira santa, 20/04 (seg) emenda sugerida de
Tiradentes (21/04, ter), 04/06 Corpus Christi (facultativo).
"""

from datetime import date, datetime, time, timedelta

import pytest

from folha_ponto.dominio import (
    DataEspecial,
    ErroDeValidacao,
    Lancamento,
    Marcacao,
    Marcacoes,
    Mes,
    Natureza,
    SemCalendario,
    TipoDia,
    TipoPendencia,
    bater_ponto,
    eh_dia_util,
    tipo_sugerido,
)

TIRADENTES = DataEspecial("Tiradentes", Natureza.FERIADO)
EMENDA_SUG = DataEspecial("Emenda de Tiradentes", Natureza.EMENDA_SUGERIDA)
EMENDA = DataEspecial("Emenda de Tiradentes", Natureza.EMENDA)
CORPUS = DataEspecial("Corpus Christi", Natureza.FACULTATIVO)
COMPLETO = {"entrada": "07:45", "saida_almoco": "12:00", "volta_almoco": "13:00", "saida": "14:45"}


class CalendarioFalso:
    def __init__(self, datas: dict[date, DataEspecial]):
        self.datas = datas

    def data_especial(self, dia):
        return self.datas.get(dia)


ABRIL = CalendarioFalso({
    date(2026, 4, 3): DataEspecial("Sexta-feira Santa", Natureza.FERIADO),
    date(2026, 4, 20): EMENDA_SUG,
    date(2026, 4, 21): TIRADENTES,
})


def lanc(dia, tipo=TipoDia.TRABALHO, marcacoes=COMPLETO, obs=""):
    return Lancamento(dia, tipo, Marcacoes.de_textos(marcacoes), obs)


# ---- UC01: bater o ponto ------------------------------------------------------
def test_primeiro_toque_cria_o_lancamento_e_grava_a_entrada():
    agora = datetime(2026, 5, 4, 7, 46, 59)
    lancamento, marcacao = bater_ponto(None, agora, TipoDia.TRABALHO)
    assert marcacao is Marcacao.ENTRADA
    assert lancamento.data == date(2026, 5, 4) and lancamento.marcacoes.entrada == time(7, 46)


def test_toques_seguintes_seguem_a_ordem_do_dia_ate_a_extra():
    lancamento, ordem = None, []
    for h, m in [(7, 45), (12, 0), (13, 0), (14, 45), (15, 0), (16, 0)]:
        lancamento, marcacao = bater_ponto(lancamento, datetime(2026, 5, 4, h, m), TipoDia.TRABALHO)
        ordem.append(marcacao)
    assert ordem == list(Marcacao)
    assert lancamento.horas == timedelta(hours=7)


def test_com_tudo_preenchido_pede_para_editar():
    cheio = lanc(date(2026, 5, 4), marcacoes={**COMPLETO, "entrada_extra": "15:00", "saida_extra": "16:00"})
    with pytest.raises(ErroDeValidacao, match="Edite o dia"):
        bater_ponto(cheio, datetime(2026, 5, 4, 17, 0), TipoDia.TRABALHO)


def test_hora_fora_de_ordem_nao_grava():
    dia = lanc(date(2026, 5, 4), marcacoes={"entrada": "07:45"})
    with pytest.raises(ErroDeValidacao):
        bater_ponto(dia, datetime(2026, 5, 4, 7, 30), TipoDia.TRABALHO)


def test_so_bate_no_lancamento_de_hoje():
    ontem = lanc(date(2026, 5, 3), marcacoes={"entrada": "07:45"})
    with pytest.raises(ErroDeValidacao):
        bater_ponto(ontem, datetime(2026, 5, 4, 8, 0), TipoDia.TRABALHO)


def test_proxima_vazia_respeita_lacunas_preenchidas_a_mao():
    m = Marcacoes.de_textos({"entrada": "07:45", "volta_almoco": "13:00"})
    assert m.proxima_vazia() is Marcacao.SAIDA


# ---- RN06 / RN07 ------------------------------------------------------------
@pytest.mark.parametrize("dia, especial, facultativo_e_folga, esperado", [
    (date(2026, 4, 21), TIRADENTES, True, TipoDia.FERIADO),
    (date(2026, 4, 20), EMENDA_SUG, True, TipoDia.FOLGA),
    (date(2026, 4, 20), EMENDA, True, TipoDia.FOLGA),
    (date(2026, 6, 4), CORPUS, True, TipoDia.FOLGA),
    (date(2026, 6, 4), CORPUS, False, TipoDia.TRABALHO),
    (date(2026, 5, 9), None, True, TipoDia.FOLGA),       # sábado
    (date(2026, 5, 4), None, True, TipoDia.TRABALHO),    # segunda comum
])
def test_tipo_sugerido(dia, especial, facultativo_e_folga, esperado):
    assert tipo_sugerido(dia, especial, facultativo_e_folga) is esperado


@pytest.mark.parametrize("dia, especial, facultativo_e_folga, util", [
    (date(2026, 5, 4), None, True, True),
    (date(2026, 5, 9), None, True, False),
    (date(2026, 4, 21), TIRADENTES, True, False),
    (date(2026, 4, 20), EMENDA, True, False),
    (date(2026, 4, 20), EMENDA_SUG, True, True),   # sugerida: útil até confirmar
    (date(2026, 6, 4), CORPUS, True, False),       # facultativo é folga (padrão)
    (date(2026, 6, 4), CORPUS, False, True),       # ...a menos que a preferência desligue
])
def test_dia_util(dia, especial, facultativo_e_folga, util):
    assert eh_dia_util(dia, especial, facultativo_e_folga) is util


# ---- UC07: pendências ---------------------------------------------------------
def test_pendencias_de_abril():
    mes = Mes(2026, 4, [
        lanc(date(2026, 4, 1)),
        lanc(date(2026, 4, 2), marcacoes={"entrada": "07:45", "saida_almoco": "12:00"}),
        lanc(date(2026, 4, 21), TipoDia.FERIADO, {}),
    ], ABRIL)
    pend = {(p.data.day, p.tipo) for p in mes.pendencias(hoje=date(2026, 4, 22))}

    assert (2, TipoPendencia.INCOMPLETO) in pend
    assert (20, TipoPendencia.EMENDA_A_CONFIRMAR) in pend
    assert (6, TipoPendencia.SEM_LANCAMENTO) in pend
    assert not {d for d, _ in pend} & {1, 3, 4, 5, 21}   # lançado, feriado, fim de semana
    assert max(d for d, _ in pend) == 22                 # até hoje, inclusive


def test_pendencia_incompleta_diz_o_que_falta():
    mes = Mes(2026, 4, [lanc(date(2026, 4, 1), marcacoes={"entrada": "07:45", "saida_almoco": "12:00"})], ABRIL)
    [pendencia] = mes.pendencias(hoje=date(2026, 4, 1))
    assert pendencia.descricao == "Falta: volta almoço, saída"


def test_emenda_resolvida_com_lancamento_nao_e_pendencia():
    mes = Mes(2026, 4, [lanc(date(2026, 4, 20), TipoDia.FOLGA, {})], ABRIL)
    assert all(p.data != date(2026, 4, 20) for p in mes.pendencias(hoje=date(2026, 4, 30)))


# ---- UC08 / RN10: a folha ------------------------------------------------------
def test_folha_lista_todos_os_dias_do_mes():
    assert [l.dia for l in Mes(2026, 2, [], SemCalendario()).folha()] == list(range(1, 29))
    assert len(Mes(2026, 4, [], ABRIL).folha()) == 30


def test_folha_na_ordem_do_papel():
    mes = Mes(2026, 4, [lanc(date(2026, 4, 1), marcacoes={**COMPLETO, "entrada_extra": "15:00",
                                                          "saida_extra": "16:00"}, obs="reunião")], ABRIL)
    linha = mes.folha()[0]
    assert linha.manha == (time(7, 45), time(12, 0))
    assert linha.tarde == (time(13, 0), time(14, 45))
    assert linha.extra == (time(15, 0), time(16, 0))
    assert linha.observacao == "reunião"
    assert linha.horas == timedelta(hours=7)


def test_observacoes_da_folha():
    mes = Mes(2026, 4, [
        lanc(date(2026, 4, 21), TipoDia.FERIADO, {}),
        lanc(date(2026, 4, 20), TipoDia.FOLGA, {}, obs="combinado com o RH"),
        lanc(date(2026, 4, 6), TipoDia.ATIVIDADE_TEORICA, {}),
    ], ABRIL)
    obs = {l.dia: l.observacao for l in mes.folha()}
    assert obs[21] == "Feriado — Tiradentes"
    assert obs[20] == "Folga — Emenda de Tiradentes · combinado com o RH"
    assert obs[6] == "Atividade teórica"
    assert obs[3] == "Feriado — Sexta-feira Santa"   # sem lançamento: vem do calendário
    assert obs[4] == "Sábado" and obs[5] == "Domingo"
    assert obs[7] == ""                               # útil sem lançamento: em branco


def test_facultativo_na_folha_depende_da_preferencia():
    cal = CalendarioFalso({date(2026, 6, 4): CORPUS})
    assert Mes(2026, 6, [], cal).folha()[3].observacao == "Ponto facultativo — Corpus Christi"
    assert Mes(2026, 6, [], cal, facultativo_e_folga=False).folha()[3].observacao == ""


# ---- resumo -----------------------------------------------------------------
def test_resumo_do_mes():
    mes = Mes(2026, 4, [
        lanc(date(2026, 4, 1)),
        lanc(date(2026, 4, 2), marcacoes={**COMPLETO, "saida": "15:45"}),
        lanc(date(2026, 4, 6), marcacoes={"entrada": "07:45"}),
    ], ABRIL)
    resumo = mes.resumo(hoje=date(2026, 4, 30))
    assert resumo.dias_uteis == 22 - 2            # 22 dias de seg a sex, menos 03/04 e 21/04
    assert resumo.dias_lancados == 3
    assert resumo.horas == timedelta(hours=13)
    assert resumo.saldo == timedelta(hours=1)


# ---- integridade --------------------------------------------------------------
def test_lancamento_de_outro_mes_e_rejeitado():
    with pytest.raises(ErroDeValidacao):
        Mes(2026, 4, [lanc(date(2026, 5, 1))], ABRIL)


def test_dois_lancamentos_na_mesma_data_sao_rejeitados():
    with pytest.raises(ErroDeValidacao, match="RN04"):
        Mes(2026, 4, [lanc(date(2026, 4, 1)), lanc(date(2026, 4, 1))], ABRIL)
