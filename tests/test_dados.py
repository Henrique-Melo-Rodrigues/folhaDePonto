"""Repositório SQLite (WP3): lançamentos, calendário, preferências e migrações."""

import sqlite3
import threading
from datetime import date, datetime, time, timedelta, timezone

import pytest

from folha_ponto.dados import (
    VERSAO_ATUAL,
    BancoMaisNovoQueOApp,
    DataDoCalendario,
    Origem,
    Repositorio,
    caminho_do_banco,
)
from folha_ponto.dominio import Jornada, Lancamento, Marcacoes, Mes, Natureza, TipoDia, TipoPendencia
from folha_ponto.dominio.preferencias import Preferencias

BRT = timezone(timedelta(hours=-3))
COMPLETO = {"entrada": "07:45", "saida_almoco": "12:00", "volta_almoco": "13:00", "saida": "14:45"}


class Relogio:
    def __init__(self):
        self.agora = datetime(2026, 4, 1, 8, 0, tzinfo=BRT)

    def __call__(self):
        return self.agora

    def avancar(self, **kw):
        self.agora += timedelta(**kw)


@pytest.fixture
def relogio():
    return Relogio()


@pytest.fixture
def repo(relogio):
    with Repositorio(":memory:", relogio=relogio) as r:
        yield r


def lanc(dia, tipo=TipoDia.TRABALHO, marcacoes=COMPLETO, obs=""):
    return Lancamento(dia, tipo, Marcacoes.de_textos(marcacoes), obs)


def auto(dia, nome, natureza=Natureza.FERIADO, origem=Origem.NACIONAL):
    return DataDoCalendario(dia, nome, natureza, origem, fonte="holidays 0.108")


# ---- migrações -------------------------------------------------------------
def test_banco_novo_nasce_na_versao_atual(repo):
    assert repo.versao == VERSAO_ATUAL == 1


def test_reabrir_o_arquivo_mantem_os_dados(tmp_path):
    caminho = tmp_path / "sub" / "folha.db"
    with Repositorio(caminho) as r:
        r.salvar(lanc(date(2026, 4, 1)))
    with Repositorio(caminho) as r:
        assert r.obter(date(2026, 4, 1)).marcacoes.saida == time(14, 45)
        assert r.versao == VERSAO_ATUAL


def test_banco_de_versao_futura_e_recusado(tmp_path):
    caminho = tmp_path / "futuro.db"
    sqlite3.connect(caminho).execute("PRAGMA user_version = 99").connection.close()
    with pytest.raises(BancoMaisNovoQueOApp):
        Repositorio(caminho)


# ---- lançamentos -------------------------------------------------------------
def test_ida_e_volta_preserva_o_lancamento(repo):
    original = lanc(date(2026, 4, 1), marcacoes={**COMPLETO, "entrada_extra": "15:00", "saida_extra": "16:30"},
                    obs="reunião com o RH")
    repo.salvar(original)
    assert repo.obter(date(2026, 4, 1)) == original


def test_obter_inexistente_devolve_none(repo):
    assert repo.obter(date(2026, 4, 1)) is None


def test_salvar_de_novo_substitui_e_preserva_criado_em(repo, relogio):
    repo.salvar(lanc(date(2026, 4, 1), marcacoes={"entrada": "07:45"}))
    criado = repo.carimbos(date(2026, 4, 1))
    relogio.avancar(hours=7)
    repo.salvar(lanc(date(2026, 4, 1)))

    depois = repo.carimbos(date(2026, 4, 1))
    assert repo.obter(date(2026, 4, 1)).marcacoes.saida == time(14, 45)
    assert depois.criado_em == criado.criado_em
    assert depois.atualizado_em - criado.criado_em == timedelta(hours=7)
    assert len(repo.listar_mes(2026, 4)) == 1          # RN04: um por data


def test_listar_mes_filtra_e_ordena(repo):
    for d in (date(2026, 4, 27), date(2026, 4, 3), date(2026, 5, 1), date(2026, 3, 31)):
        repo.salvar(lanc(d))
    assert [l.data.day for l in repo.listar_mes(2026, 4)] == [3, 27]


def test_apagar(repo):
    repo.salvar(lanc(date(2026, 4, 1)))
    assert repo.apagar(date(2026, 4, 1)) is True
    assert repo.apagar(date(2026, 4, 1)) is False
    assert repo.obter(date(2026, 4, 1)) is None


def test_dia_sem_horarios_volta_vazio(repo):
    repo.salvar(lanc(date(2026, 4, 21), TipoDia.FERIADO, {}))
    dia = repo.obter(date(2026, 4, 21))
    assert dia.marcacoes.vazia and dia.tipo is TipoDia.FERIADO


def test_erro_no_meio_da_transacao_desfaz_tudo(repo):
    repo.salvar(lanc(date(2026, 4, 1)))

    def falha(c):
        c.execute("DELETE FROM lancamentos")
        raise RuntimeError("queda de energia")

    with pytest.raises(RuntimeError):
        repo._transacao(falha)
    assert repo.obter(date(2026, 4, 1)) is not None


def test_acesso_de_varias_threads(repo):
    erros = []

    def bater(dia):
        try:
            repo.salvar(lanc(date(2026, 4, dia)))
        except Exception as e:  # pragma: no cover - só aparece se a trava falhar
            erros.append(e)

    threads = [threading.Thread(target=bater, args=(d,)) for d in range(1, 29)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not erros and len(repo.listar_mes(2026, 4)) == 28


# ---- calendário -------------------------------------------------------------
def test_substituir_calendario_automatico_preserva_manuais_e_ocultas(repo):
    repo.substituir_calendario_automatico(2026, [
        auto(date(2026, 4, 21), "Tiradentes"),
        auto(date(2026, 6, 4), "Corpus Christi", Natureza.FACULTATIVO, Origem.FACULTATIVO),
        auto(date(2026, 4, 20), "Emenda de Tiradentes", Natureza.EMENDA_SUGERIDA, Origem.REGRA_EMENDA),
    ])
    repo.salvar_data_manual(DataDoCalendario(date(2026, 4, 9), "Aniversário da cidade", Natureza.FERIADO,
                                             Origem.MANUAL, recorrente=True))
    repo.ocultar_data(date(2026, 6, 4), "Corpus Christi")

    # recalcular (UC06 1'): sai Tiradentes, entra a Sexta-feira Santa
    repo.substituir_calendario_automatico(2026, [
        auto(date(2026, 4, 3), "Sexta-feira Santa"),
        auto(date(2026, 6, 4), "Corpus Christi", Natureza.FACULTATIVO, Origem.FACULTATIVO),
    ])
    nomes = {d.nome: d for d in repo.datas_do_periodo(date(2026, 1, 1), date(2026, 12, 31), incluir_ocultas=True)}
    assert set(nomes) == {"Sexta-feira Santa", "Corpus Christi", "Aniversário da cidade"}
    assert nomes["Corpus Christi"].oculta is True                     # ocultação sobrevive
    assert nomes["Sexta-feira Santa"].fonte == "holidays 0.108"        # RN09
    assert repo.anos_com_calendario() == {2026}


def test_emenda_confirmada_nao_volta_a_ser_sugestao(repo):
    sugestao = auto(date(2026, 4, 20), "Emenda de Tiradentes", Natureza.EMENDA_SUGERIDA, Origem.REGRA_EMENDA)
    repo.substituir_calendario_automatico(2026, [sugestao])
    repo.salvar_data_manual(DataDoCalendario(date(2026, 4, 20), "Emenda de Tiradentes", Natureza.EMENDA, Origem.MANUAL))
    repo.substituir_calendario_automatico(2026, [sugestao])
    [d] = repo.datas_do_periodo(date(2026, 4, 20), date(2026, 4, 20))
    assert d.natureza is Natureza.EMENDA and d.origem is Origem.MANUAL


def test_substituir_recusa_data_de_outro_ano_ou_manual(repo):
    with pytest.raises(ValueError):
        repo.substituir_calendario_automatico(2026, [auto(date(2027, 1, 1), "Ano novo")])
    with pytest.raises(ValueError):
        repo.substituir_calendario_automatico(2026, [auto(date(2026, 1, 1), "x", origem=Origem.MANUAL)])


def test_recorrente_aparece_em_todos_os_anos(repo):
    repo.salvar_data_manual(DataDoCalendario(date(2026, 4, 9), "Aniversário da cidade", Natureza.FERIADO,
                                             Origem.MANUAL, recorrente=True))
    datas = repo.datas_do_periodo(date(2027, 1, 1), date(2028, 12, 31))
    assert [d.data for d in datas] == [date(2027, 4, 9), date(2028, 4, 9)]


def test_apagar_data_manual_nao_apaga_automatica(repo):
    repo.substituir_calendario_automatico(2026, [auto(date(2026, 4, 21), "Tiradentes")])
    assert repo.apagar_data_manual(date(2026, 4, 21), "Tiradentes") is False
    repo.salvar_data_manual(DataDoCalendario(date(2026, 4, 9), "Local", Natureza.FERIADO, Origem.MANUAL))
    assert repo.apagar_data_manual(date(2026, 4, 9), "Local") is True


def test_calendario_do_mes_aplica_precedencia_e_ignora_ocultas(repo):
    repo.substituir_calendario_automatico(2026, [
        auto(date(2026, 4, 21), "Tiradentes"),
        auto(date(2026, 4, 21), "Véspera qualquer", Natureza.FACULTATIVO, Origem.FACULTATIVO),
        auto(date(2026, 4, 20), "Emenda de Tiradentes", Natureza.EMENDA_SUGERIDA, Origem.REGRA_EMENDA),
        auto(date(2026, 4, 3), "Sexta-feira Santa"),
    ])
    repo.ocultar_data(date(2026, 4, 3), "Sexta-feira Santa")
    cal = repo.calendario_do_mes(2026, 4)
    assert cal.data_especial(date(2026, 4, 21)).natureza is Natureza.FERIADO
    assert cal.data_especial(date(2026, 4, 20)).natureza is Natureza.EMENDA_SUGERIDA
    assert cal.data_especial(date(2026, 4, 3)) is None
    assert repo.calendario_do_mes(2026, 12).data_especial(date(2026, 12, 31)) is None


def test_repositorio_alimenta_o_mes_do_dominio(repo):
    """Integração: domínio (WP2) + banco (WP3)."""
    repo.substituir_calendario_automatico(2026, [auto(date(2026, 4, 21), "Tiradentes")])
    repo.salvar(lanc(date(2026, 4, 1)))
    mes = Mes(2026, 4, repo.listar_mes(2026, 4), repo.calendario_do_mes(2026, 4))
    assert mes.folha()[20].observacao == "Feriado — Tiradentes"
    tipos = {p.tipo for p in mes.pendencias(hoje=date(2026, 4, 2))}
    assert tipos == {TipoPendencia.SEM_LANCAMENTO}


# ---- preferências -------------------------------------------------------------
def test_preferencias_padrao(repo):
    p = repo.preferencias()
    assert (p.uf, p.municipio, p.facultativo_e_folga) == ("SP", "Cubatão", True)
    assert p.jornada.duracao == timedelta(hours=6)


def test_preferencias_ida_e_volta(repo):
    nova = Preferencias(uf="rj", municipio=" Niterói ", jornada=Jornada(time(8), time(12), time(13), time(17)),
                        facultativo_e_folga=False, tema="escuro")
    repo.salvar_preferencias(nova)
    lida = repo.preferencias()
    assert lida == nova and lida.uf == "RJ" and lida.municipio == "Niterói"


def test_preferencia_desconhecida_no_banco_e_ignorada(repo):
    repo._transacao(lambda c: c.execute("INSERT INTO preferencias VALUES ('chave_antiga', '1')"))
    assert repo.preferencias().uf == "SP"


# ---- onde fica o banco ---------------------------------------------------------
def test_caminho_do_banco(monkeypatch, tmp_path):
    monkeypatch.delenv("FOLHA_PONTO_DB", raising=False)
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    assert caminho_do_banco() == tmp_path / "folha_de_ponto.db"
    monkeypatch.setenv("FOLHA_PONTO_DB", str(tmp_path / "x.db"))
    assert caminho_do_banco() == tmp_path / "x.db"
    monkeypatch.delenv("FOLHA_PONTO_DB")
    monkeypatch.delenv("FLET_APP_STORAGE_DATA")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert caminho_do_banco() == tmp_path / "folha-ponto" / "folha_de_ponto.db"
