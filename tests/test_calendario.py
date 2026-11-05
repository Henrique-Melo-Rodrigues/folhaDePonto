"""Calendário (WP4): lib holidays BR/SP, emendas (RN05), preparo do ano (UC06), UC03 e UC10."""

from datetime import date

import pytest

from folha_ponto.calendario import (
    FONTE,
    calendario_oficial,
    cadastrar_data,
    confirmar_emenda,
    descartar_emenda,
    emendas_candidatas,
    garantir_ano,
    ocultar_data,
    preparar_ano,
    remover_data,
    uf_conhecida,
)
from folha_ponto.dados import Origem, Repositorio
from folha_ponto.dominio import DataEspecial, ErroDeValidacao, Mes, Natureza, TipoDia, TipoPendencia
from folha_ponto.dominio.preferencias import Preferencias
from folha_ponto.dominio.registro import tipo_sugerido


@pytest.fixture
def repo():
    with Repositorio(":memory:") as r:
        yield r


def feriado(nome):
    return DataEspecial(nome, Natureza.FERIADO)


# ---- calendário oficial (lib holidays) ---------------------------------------
def test_feriados_nacionais_e_estaduais_de_sp_com_origem():
    oficial = calendario_oficial(2026, "SP")
    por_dia = {(d.data, d.nome): d for d in oficial.datas}
    assert por_dia[(date(2026, 4, 21), "Tiradentes")].origem == "nacional"
    revolucao = por_dia[(date(2026, 7, 9), "Revolução Constitucionalista")]
    assert (revolucao.natureza, revolucao.origem) == (Natureza.FERIADO, "estadual")
    assert oficial.aviso == ""
    assert oficial.fonte == FONTE and FONTE.startswith("holidays ")


def test_pontos_facultativos_vem_da_categoria_optional():
    facultativos = {d.data: d.nome for d in calendario_oficial(2026).datas if d.natureza is Natureza.FACULTATIVO}
    assert facultativos[date(2026, 6, 4)] == "Corpus Christi"
    assert facultativos[date(2026, 10, 28)] == "Dia do Servidor Público"
    assert {date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18)} <= facultativos.keys()
    assert all(d.origem == "facultativo" for d in calendario_oficial(2026).datas if d.natureza is Natureza.FACULTATIVO)


def test_uf_desconhecida_usa_so_os_nacionais_e_avisa():
    """UC06 E1."""
    oficial = calendario_oficial(2026, "XX")
    assert "XX" in oficial.aviso
    assert date(2026, 7, 9) not in {d.data for d in oficial.datas}
    assert date(2026, 4, 21) in {d.data for d in oficial.datas}
    assert uf_conhecida("sp") and not uf_conhecida("XX")


# ---- RN05 (puro) ---------------------------------------------------------------
def test_emendas_de_2026_do_exemplo_da_rn05():
    datas = [(d.data, DataEspecial(d.nome, d.natureza)) for d in calendario_oficial([2025, 2026, 2027]).datas]
    em_2026 = [c for c in emendas_candidatas(datas) if c.data.year == 2026]
    assert [c.data for c in em_2026] == [date(2026, 1, 2), date(2026, 4, 20), date(2026, 6, 5), date(2026, 7, 10)]
    tiradentes = em_2026[1]
    assert (tiradentes.motivo, tiradentes.nome) == (date(2026, 4, 21), "Tiradentes (terça, 21/04)")


def test_candidato_que_ja_e_folga_nao_vira_emenda():
    # Carnaval: terça 17/02/2026, mas a segunda 16/02 também é Carnaval.
    datas = [(date(2026, 2, 16), DataEspecial("Carnaval", Natureza.FACULTATIVO)),
             (date(2026, 2, 17), DataEspecial("Carnaval", Natureza.FACULTATIVO))]
    assert emendas_candidatas(datas) == []


def test_facultativo_so_gera_emenda_se_for_folga():
    corpus = [(date(2026, 6, 4), DataEspecial("Corpus Christi", Natureza.FACULTATIVO))]
    assert [c.data for c in emendas_candidatas(corpus)] == [date(2026, 6, 5)]
    assert emendas_candidatas(corpus, facultativo_e_folga=False) == []


def test_so_terca_e_quinta_geram_emenda_e_sugestao_nao_gera_outra():
    datas = [(date(2026, 11, 2), feriado("Finados")),                 # segunda
             (date(2026, 11, 20), feriado("Consciência Negra")),      # sexta
             (date(2026, 4, 14), DataEspecial("x", Natureza.EMENDA_SUGERIDA))]  # terça, mas é sugestão
    assert emendas_candidatas(datas) == []


def test_emenda_atravessa_a_virada_do_ano():
    # 01/01/2030 é terça: a emenda é a segunda 31/12/2029.
    [c] = emendas_candidatas([(date(2030, 1, 1), feriado("Confraternização Universal"))])
    assert c.data == date(2029, 12, 31)


# ---- UC06 ------------------------------------------------------------------------
def test_preparar_ano_grava_feriados_facultativos_e_sugestoes(repo):
    resultado = preparar_ano(repo, 2026)
    assert resultado.feriados == 11 and resultado.facultativos == 7 and resultado.aviso == ""
    assert repo.anos_com_calendario() == {2026}

    abril = repo.calendario_do_mes(2026, 4)
    assert abril.data_especial(date(2026, 4, 21)) == feriado("Tiradentes")
    assert abril.data_especial(date(2026, 4, 20)).natureza is Natureza.EMENDA_SUGERIDA

    [emenda] = [d for d in repo.datas_do_periodo(date(2026, 4, 20), date(2026, 4, 20))]
    assert emenda.origem is Origem.REGRA_EMENDA and FONTE in emenda.fonte  # RN09
    [rev] = repo.datas_do_periodo(date(2026, 7, 9), date(2026, 7, 9))
    assert (rev.origem, rev.fonte) == (Origem.ESTADUAL, FONTE)


def test_emenda_de_31_12_vinda_do_ano_seguinte_fica_no_ano_certo(repo):
    # 01/01/2030 é terça. Com facultativo = folga, 31/12 já é a Véspera de Ano-Novo (não é útil).
    preparar_ano(repo, 2029)
    naturezas = {d.natureza for d in repo.datas_do_periodo(date(2029, 12, 31), date(2029, 12, 31))}
    assert naturezas == {Natureza.FACULTATIVO}

    preparar_ano(repo, 2029, Preferencias(facultativo_e_folga=False))
    naturezas = {d.natureza for d in repo.datas_do_periodo(date(2029, 12, 31), date(2029, 12, 31))}
    assert naturezas == {Natureza.FACULTATIVO, Natureza.EMENDA_SUGERIDA}
    assert repo.anos_com_calendario() == {2029}


def test_garantir_ano_so_prepara_uma_vez(repo):
    assert garantir_ano(repo, 2026) is not None
    assert garantir_ano(repo, 2026) is None


def test_preferencia_de_facultativo_desligada_tira_a_emenda_de_corpus_christi(repo):
    preparar_ano(repo, 2026, Preferencias(facultativo_e_folga=False))
    junho = repo.calendario_do_mes(2026, 6)
    assert junho.data_especial(date(2026, 6, 5)) is None
    assert junho.data_especial(date(2026, 6, 4)).natureza is Natureza.FACULTATIVO


def test_uf_invalida_gravada_nao_impede_o_preparo(repo):
    resultado = preparar_ano(repo, 2026, Preferencias(uf="XX"))
    assert resultado.aviso and resultado.feriados == 10


def test_mes_com_calendario_preparado_mostra_pendencias_e_folha(repo):
    preparar_ano(repo, 2026)
    abril = Mes(2026, 4, [], repo.calendario_do_mes(2026, 4))
    pendencias = {p.data: p.tipo for p in abril.pendencias(hoje=date(2026, 4, 30))}
    assert pendencias[date(2026, 4, 20)] is TipoPendencia.EMENDA_A_CONFIRMAR
    assert date(2026, 4, 21) not in pendencias and date(2026, 4, 3) not in pendencias
    assert abril.folha()[20].observacao == "Feriado — Tiradentes"


# ---- UC03 ------------------------------------------------------------------------
def test_confirmar_emenda_vira_folga_e_sobrevive_ao_recalcular(repo):
    preparar_ano(repo, 2026)
    confirmada = confirmar_emenda(repo, date(2026, 4, 20))
    assert (confirmada.natureza, confirmada.origem) == (Natureza.EMENDA, Origem.MANUAL)

    preparar_ano(repo, 2026)  # "Recalcular calendário"
    especial = repo.calendario_do_mes(2026, 4).data_especial(date(2026, 4, 20))
    assert especial.natureza is Natureza.EMENDA
    assert tipo_sugerido(date(2026, 4, 20), especial) is TipoDia.FOLGA
    abril = Mes(2026, 4, [], repo.calendario_do_mes(2026, 4))
    assert not abril.eh_dia_util(date(2026, 4, 20))  # RN07
    assert date(2026, 4, 20) not in {p.data for p in abril.pendencias(date(2026, 4, 30))}


def test_descartar_emenda_volta_a_ser_dia_util_e_sobrevive_ao_recalcular(repo):
    preparar_ano(repo, 2026)
    descartar_emenda(repo, date(2026, 4, 20))
    preparar_ano(repo, 2026)
    abril = Mes(2026, 4, [], repo.calendario_do_mes(2026, 4))
    assert abril.especial(date(2026, 4, 20)) is None
    pendencias = {p.data: p.tipo for p in abril.pendencias(date(2026, 4, 30))}
    assert pendencias[date(2026, 4, 20)] is TipoPendencia.SEM_LANCAMENTO


def test_confirmar_dia_que_nao_e_emenda_candidata_e_erro(repo):
    preparar_ano(repo, 2026)
    with pytest.raises(ErroDeValidacao):
        confirmar_emenda(repo, date(2026, 4, 22))


# ---- UC10 ------------------------------------------------------------------------
def test_feriado_municipal_cadastrado_gera_emenda_e_e_recorrente(repo):
    preparar_ano(repo, 2026)
    # Data fictícia de teste: uma quinta em 2026 (as datas reais de Cubatão ainda vão ser confirmadas).
    cadastrar_data(repo, date(2026, 3, 12), "Feriado municipal de teste", recorrente=True)
    marco = repo.calendario_do_mes(2026, 3)
    assert marco.data_especial(date(2026, 3, 12)) == feriado("Feriado municipal de teste")
    assert marco.data_especial(date(2026, 3, 13)).natureza is Natureza.EMENDA_SUGERIDA
    assert repo.calendario_do_mes(2027, 3).data_especial(date(2027, 3, 12)) is not None

    assert remover_data(repo, date(2026, 3, 12), "Feriado municipal de teste")
    assert repo.calendario_do_mes(2026, 3).data_especial(date(2026, 3, 13)) is None


def test_ocultar_facultativo_desfaz_a_emenda(repo):
    preparar_ano(repo, 2026)
    assert ocultar_data(repo, date(2026, 6, 4), "Corpus Christi")
    junho = repo.calendario_do_mes(2026, 6)
    assert junho.data_especial(date(2026, 6, 4)) is None
    assert junho.data_especial(date(2026, 6, 5)) is None
    preparar_ano(repo, 2026)
    assert repo.calendario_do_mes(2026, 6).data_especial(date(2026, 6, 4)) is None


def test_cadastro_valida_nome_e_natureza(repo):
    with pytest.raises(ErroDeValidacao):
        cadastrar_data(repo, date(2026, 3, 12), "  ")
    with pytest.raises(ErroDeValidacao):
        cadastrar_data(repo, date(2026, 3, 12), "x", Natureza.EMENDA_SUGERIDA)


def test_cadastrar_antes_de_preparar_nao_prepara_o_ano(repo):
    cadastrar_data(repo, date(2026, 3, 12), "Feriado municipal de teste")
    assert repo.anos_com_calendario() == set()
