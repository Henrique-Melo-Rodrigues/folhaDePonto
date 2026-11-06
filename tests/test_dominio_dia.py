"""Regras de um dia: RN01 (horário), RN02 (ordem), RN03 (status), RN08 (horas e saldo)."""

import json
from datetime import date, time, timedelta
from pathlib import Path

import pytest

from folha_ponto.dominio import (
    JORNADA_PADRAO,
    ErroDeValidacao,
    Jornada,
    Lancamento,
    Marcacao,
    Marcacoes,
    Status,
    TipoDia,
    calcular_status,
    ler_horario,
)

CASOS_STATUS = json.loads((Path(__file__).parent / "dados" / "casos_status.json").read_text(encoding="utf-8"))
DIA_COMPLETO = {"entrada": "07:45", "saida_almoco": "12:00", "volta_almoco": "13:00", "saida": "14:45"}


# ---- RN01 -----------------------------------------------------------------
@pytest.mark.parametrize("texto, esperado", [("07:45", time(7, 45)), ("23:59", time(23, 59)), ("00:00", time(0, 0)),
                                             ("", None), ("   ", None), (None, None), (" 08:00 ", time(8, 0))])
def test_ler_horario_aceita(texto, esperado):
    assert ler_horario(texto) == esperado


@pytest.mark.parametrize("texto", ["7:45", "0745", "07h45", "24:00", "12:60", "ab:cd"])
def test_ler_horario_rejeita(texto):
    with pytest.raises(ErroDeValidacao):
        ler_horario(texto, Marcacao.ENTRADA)


def test_erro_aponta_o_campo():
    with pytest.raises(ErroDeValidacao) as erro:
        Marcacoes.de_textos({"entrada": "07:45", "saida": "25:00"})
    assert erro.value.campo is Marcacao.SAIDA


def test_marcacao_desconhecida_e_rejeitada():
    with pytest.raises(ErroDeValidacao, match="desconhecida"):
        Marcacoes.de_textos({"arrival": "07:45"})


# ---- RN02 -----------------------------------------------------------------
def test_ordem_invertida_e_rejeitada_e_aponta_a_marcacao_posterior():
    with pytest.raises(ErroDeValidacao) as erro:
        Marcacoes.de_textos({"entrada": "08:00", "saida_almoco": "07:00"})
    assert erro.value.campo is Marcacao.SAIDA_ALMOCO
    assert "depois de entrada (08:00)" in str(erro.value)


def test_horarios_iguais_sao_rejeitados():
    with pytest.raises(ErroDeValidacao):
        Marcacoes.de_textos({"entrada": "08:00", "saida": "08:00"})


def test_vazias_no_meio_sao_aceitas():
    m = Marcacoes.de_textos({"entrada": "07:45", "saida": "14:45"})
    assert m.saida_almoco is None and m.saida == time(14, 45)


def test_extra_depois_da_saida():
    with pytest.raises(ErroDeValidacao):
        Marcacoes.de_textos({**DIA_COMPLETO, "entrada_extra": "14:00"})


def test_saida_extra_exige_entrada_extra():
    with pytest.raises(ErroDeValidacao) as erro:
        Marcacoes.de_textos({**DIA_COMPLETO, "saida_extra": "17:00"})
    assert erro.value.campo is Marcacao.SAIDA_EXTRA


def test_entrada_extra_sozinha_e_hora_extra_em_andamento():
    assert Marcacoes.de_textos({**DIA_COMPLETO, "entrada_extra": "15:00"}).saida_extra is None


def test_marcacao_com_segundos_e_rejeitada():
    with pytest.raises(ErroDeValidacao):
        Marcacoes(entrada=time(7, 45, 30))


def test_com_revalida_a_ordem():
    m = Marcacoes.de_textos(DIA_COMPLETO)
    with pytest.raises(ErroDeValidacao):
        m.com(Marcacao.SAIDA, time(9, 0))


def test_como_textos_ida_e_volta():
    textos = {**DIA_COMPLETO, "entrada_extra": "", "saida_extra": ""}
    assert Marcacoes.de_textos(textos).como_textos() == textos


# ---- RN03 (vetores golden herdados da v1) ------------------------------------
def test_ha_vetores_golden():
    assert len(CASOS_STATUS["casos"]) >= 10


@pytest.mark.parametrize("caso", CASOS_STATUS["casos"], ids=lambda c: c["nome"])
def test_status_bate_com_os_vetores_golden(caso):
    status = calcular_status(TipoDia(caso["tipo"]), Marcacoes.de_textos(caso["marcacoes"]))
    assert status == Status(caso["esperado"])


def test_lancamento_deriva_o_status():
    assert Lancamento(date(2026, 5, 4), TipoDia.TRABALHO).status is Status.INCOMPLETO
    assert Lancamento(date(2026, 5, 4), TipoDia.FOLGA).status is Status.NAO_TRABALHADO


# ---- RN08 -----------------------------------------------------------------
def test_jornada_padrao_e_de_seis_horas():
    assert JORNADA_PADRAO.duracao == timedelta(hours=6)


def test_horas_de_um_dia_completo():
    dia = Lancamento(date(2026, 5, 4), TipoDia.TRABALHO, Marcacoes.de_textos(DIA_COMPLETO))
    assert dia.horas == timedelta(hours=6)
    assert dia.saldo() == timedelta(0)


def test_hora_extra_entra_nas_horas_e_no_saldo():
    dia = Lancamento(date(2026, 5, 4), TipoDia.TRABALHO,
                     Marcacoes.de_textos({**DIA_COMPLETO, "entrada_extra": "15:00", "saida_extra": "16:30"}))
    assert dia.horas == timedelta(hours=7, minutes=30)
    assert dia.saldo() == timedelta(hours=1, minutes=30)


def test_extra_em_andamento_nao_conta():
    dia = Lancamento(date(2026, 5, 4), TipoDia.TRABALHO,
                     Marcacoes.de_textos({**DIA_COMPLETO, "entrada_extra": "15:00"}))
    assert dia.horas == timedelta(hours=6)


def test_dia_incompleto_nao_tem_horas_nem_saldo():
    dia = Lancamento(date(2026, 5, 4), TipoDia.TRABALHO, Marcacoes.de_textos({"entrada": "07:45"}))
    assert dia.horas is None and dia.saldo() is None


def test_saida_antecipada_gera_saldo_negativo():
    dia = Lancamento(date(2026, 5, 4), TipoDia.TRABALHO, Marcacoes.de_textos({**DIA_COMPLETO, "saida": "14:15"}))
    assert dia.saldo() == timedelta(minutes=-30)


def test_trabalho_na_folga_e_todo_saldo():
    dia = Lancamento(date(2026, 5, 9), TipoDia.FOLGA, Marcacoes.de_textos(DIA_COMPLETO))
    assert dia.saldo() == timedelta(hours=6)


def test_jornada_configuravel():
    jornada = Jornada(time(8, 0), time(12, 0), time(13, 0), time(17, 0))
    assert jornada.duracao == timedelta(hours=8)


# ---- Lançamento -------------------------------------------------------------
def test_observacao_e_aparada_e_tipo_aceita_texto():
    dia = Lancamento(date(2026, 5, 4), "folga", observacao="  médico  ")
    assert dia.tipo is TipoDia.FOLGA and dia.observacao == "médico"


def test_tipo_invalido_e_rejeitado():
    with pytest.raises(ValueError):
        Lancamento(date(2026, 5, 4), "ferias")


def test_vocabulario_tem_rotulos():
    assert TipoDia.ATIVIDADE_TEORICA.rotulo == "Atividade teórica"
    assert Status.NAO_TRABALHADO.rotulo == "Não trabalhado"
    assert [m.rotulo for m in Marcacao][-2:] == ["Entrada extra", "Saída extra"]
