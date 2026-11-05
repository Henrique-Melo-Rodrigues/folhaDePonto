"""Exportação (WP6): folha em texto/CSV (UC08 2') e backup/restauração (UC09)."""

import csv
import io
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from folha_ponto.dados import Repositorio
from folha_ponto.dominio import Natureza, TipoDia
from folha_ponto.dominio.preferencias import Preferencias
from folha_ponto.exportacao import COLUNAS_CSV, FORMATO, VERSAO, ErroDeBackup, gerar_backup, ler_backup
from folha_ponto.ui.servicos import Servicos

BRT = timezone(timedelta(hours=-3))
COMPLETO = {"entrada": "07:45", "saida_almoco": "12:00", "volta_almoco": "13:00", "saida": "14:45"}


class Relogio:
    def __init__(self, agora):
        self.agora = agora

    def __call__(self):
        return self.agora

    def avancar(self, **kw):
        self.agora += timedelta(**kw)


@pytest.fixture
def relogio():
    return Relogio(datetime(2026, 4, 22, 8, 0, tzinfo=BRT))


def novo_app(relogio):
    repo = Repositorio(":memory:", relogio=relogio)
    return Servicos(repo, relogio)


@pytest.fixture
def app(relogio):
    a = novo_app(relogio)
    yield a
    a.repo.fechar()


def popular(app):
    app.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, {**COMPLETO, "entrada_extra": "18:00", "saida_extra": "19:00"},
                   "plantão")
    app.salvar_dia(date(2026, 4, 2), TipoDia.TRABALHO, {"entrada": "07:45"})
    app.salvar_dia(date(2026, 4, 20), TipoDia.FOLGA, {}, "Emenda")          # confirma a emenda (UC03)
    app.cadastrar_data("12/03/2026", "Feriado municipal de teste", "feriado", recorrente=True)
    app.ocultar_data(date(2026, 10, 28), "Dia do Servidor Público")
    app.salvar_dia(date(2026, 6, 5), TipoDia.TRABALHO, COMPLETO)           # descarta a emenda de Corpus Christi
    app.salvar_preferencias(uf="SP", municipio="Cubatão", jornada=COMPLETO, facultativo_e_folga=True, tema="escuro")


def estado(app):
    """O que o usuário vê, para comparar antes e depois da restauração."""
    lancamentos = {l.data: (l.tipo, l.marcacoes, l.observacao)
                   for m in range(1, 13) for l in app.repo.listar_mes(2026, m)}
    especiais = {d: app.especial(d) for d in (date(2026, 3, 12), date(2026, 3, 13), date(2026, 4, 20),
                                              date(2026, 6, 5), date(2026, 10, 28), date(2027, 3, 12))}
    return lancamentos, especiais, app.repo.preferencias()


# ---- backup: ida e volta ------------------------------------------------------------
def test_backup_restaura_tudo_num_aparelho_novo(app, relogio):
    popular(app)
    nome, conteudo = app.gerar_backup()
    assert nome == "backup-2026-04-22.json"
    documento = json.loads(conteudo)
    assert (documento["formato"], documento["versao"]) == (FORMATO, VERSAO)

    novo = novo_app(relogio)
    backup = novo.ler_backup(conteudo.encode("utf-8"))
    assert backup.dias == 4
    resultado = novo.restaurar(backup, substituir=True)
    assert (resultado.lancamentos_gravados, resultado.datas_manuais) == (4, 2)  # municipal + emenda confirmada
    assert estado(novo) == estado(app)
    assert novo.repo.carimbos(date(2026, 4, 1)) == app.repo.carimbos(date(2026, 4, 1))  # created_at preservado
    assert novo.especial(date(2026, 10, 28)) is None  # a data oculta continua oculta


def test_backup_de_banco_vazio(app):
    _, conteudo = app.gerar_backup()
    backup = ler_backup(conteudo)
    assert backup.dias == 0 and backup.dados.preferencias == Preferencias()


def test_substituir_apaga_o_que_nao_esta_no_backup(app, relogio):
    _, vazio = app.gerar_backup()
    popular(app)
    app.restaurar(ler_backup(vazio), substituir=True)
    assert app.repo.listar_mes(2026, 4) == []
    assert app.datas_manuais(2026) == []
    assert app.repo.preferencias() == Preferencias() == app.preferencias
    assert app.especial(date(2026, 4, 21)).nome == "Tiradentes"  # o calendário automático foi refeito
    assert app.especial(date(2026, 4, 20)).natureza is Natureza.EMENDA_SUGERIDA


def test_mesclar_fica_com_o_lancamento_mais_recente(app, relogio):
    app.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, COMPLETO, "antigo no aparelho")
    app.salvar_dia(date(2026, 4, 2), TipoDia.TRABALHO, COMPLETO, "novo no aparelho")
    outro = novo_app(relogio)
    relogio.avancar(hours=1)
    outro.salvar_dia(date(2026, 4, 1), TipoDia.FALTA, {}, "mais novo no backup")
    outro.salvar_dia(date(2026, 4, 3), TipoDia.TRABALHO, COMPLETO, "só no backup")
    relogio.avancar(hours=1)
    app.salvar_dia(date(2026, 4, 2), TipoDia.TRABALHO, COMPLETO, "novo no aparelho")  # mais novo que o backup
    outro.salvar_dia(date(2026, 4, 2), TipoDia.TRABALHO, COMPLETO, "velho no backup")  # mesmo instante: empata
    _, conteudo = outro.gerar_backup()

    app.salvar_preferencias(uf="SP", municipio="Cubatão", jornada=COMPLETO, facultativo_e_folga=True, tema="escuro")
    resultado = app.restaurar(ler_backup(conteudo), substituir=False)
    assert (resultado.lancamentos_gravados, resultado.lancamentos_mantidos) == (2, 1)
    obs = {l.data.day: l.observacao for l in app.repo.listar_mes(2026, 4)}
    assert obs == {1: "mais novo no backup", 2: "novo no aparelho", 3: "só no backup"}
    assert app.repo.preferencias().tema == "escuro"  # mesclar não troca as preferências


def test_restauracao_com_erro_nao_grava_nada(app):
    """UC09 E1: rollback."""
    popular(app)
    _, conteudo = app.gerar_backup()
    backup = ler_backup(conteudo)
    antes = estado(app)
    object.__setattr__(backup.dados, "datas_manuais",
                       backup.dados.datas_manuais + (backup.dados.datas_ocultas[0],))  # origem automática: inválido
    with pytest.raises(ValueError):
        app.repo.importar(backup.dados, substituir=True)
    assert estado(app) == antes


# ---- backup: arquivos inválidos (UC09 E1) ----------------------------------------
@pytest.mark.parametrize("conteudo, trecho", [
    (b"\xff\xfe nao e json", "JSON"),
    ("[]", "não é um backup"),
    ('{"formato": "outro", "versao": 1}', "não é um backup"),
    (json.dumps({"formato": FORMATO, "versao": 99}), "versão 99"),
    (json.dumps({"formato": FORMATO, "versao": VERSAO, "lancamentos": {}}), "lista"),
])
def test_arquivo_invalido(conteudo, trecho):
    with pytest.raises(ErroDeBackup, match=trecho):
        ler_backup(conteudo)


def _com(alteracao):
    documento = {"formato": FORMATO, "versao": VERSAO, "lancamentos": [
        {"data": "2026-04-01", "tipo": "trabalho", **COMPLETO, "observacao": "",
         "criado_em": "2026-04-01T08:00:00-03:00", "atualizado_em": "2026-04-01T08:00:00-03:00"}]}
    alteracao(documento)
    return json.dumps(documento)


@pytest.mark.parametrize("alteracao", [
    lambda d: d["lancamentos"][0].update(saida_almoco="07:00"),            # RN02
    lambda d: d["lancamentos"][0].update(entrada="7:45"),                  # RN01
    lambda d: d["lancamentos"][0].update(tipo="ferias"),
    lambda d: d["lancamentos"][0].update(atualizado_em="2026-04-01T08:00:00"),  # sem fuso
    lambda d: d["lancamentos"].append(dict(d["lancamentos"][0])),           # RN04
    lambda d: d.update(datas_ocultas=[{"data": "2026-01-01", "nome": "x", "natureza": "feriado",
                                       "origem": "manual"}]),
    lambda d: d.update(datas_manuais=[{"data": "2026-01-01", "nome": " ", "natureza": "feriado"}]),
    lambda d: d.update(preferencias={"uf": "S"}),
    lambda d: d.update(preferencias={"jornada": {"entrada": "08:00"}}),
    lambda d: d.update(preferencias={"jornada": {"entrada": "13:00", "saida_almoco": "12:00",
                                                 "volta_almoco": "13:30", "saida": "17:00"}}),
])
def test_dado_invalido_no_backup(alteracao):
    with pytest.raises(ErroDeBackup):
        ler_backup(_com(alteracao))
    ler_backup(_com(lambda d: None))  # o documento base é válido


def test_campos_desconhecidos_sao_ignorados():
    backup = ler_backup(_com(lambda d: d.update(novidade=1, preferencias={"uf": "RJ", "cor": "azul"})))
    assert backup.dados.preferencias.uf == "RJ" and backup.dias == 1


# ---- folha em texto e CSV (UC08 2') ----------------------------------------------
def test_folha_em_csv_tem_todos_os_dias_na_ordem_do_papel(app):
    popular(app)
    nome, conteudo = app.folha_em_csv(2026, 4)
    assert nome == "folha-2026-04.csv"
    linhas = list(csv.reader(io.StringIO(conteudo), delimiter=";"))
    assert tuple(linhas[0]) == COLUNAS_CSV
    assert len(linhas) == 1 + 30  # RN10
    assert linhas[1] == ["01", "Qua", "07:45", "12:00", "13:00", "14:45", "18:00", "19:00", "plantão"]
    assert linhas[2][2:4] == ["07:45", ""]
    assert linhas[21] == ["21", "Ter", "", "", "", "", "", "", "Feriado — Tiradentes"]
    assert linhas[4][-1] == "Sábado"


def test_folha_em_texto(app):
    popular(app)
    nome, texto = app.folha_em_texto(2026, 4)
    assert nome == "folha-2026-04.txt"
    linhas = texto.splitlines()
    assert linhas[0] == "Folha de ponto — Abril 2026"
    assert "01 Qua  07:45 12:00   13:00 14:45   18:00 19:00  plantão" in linhas
    assert any(l.startswith("21 Ter") and l.endswith("Feriado — Tiradentes") for l in linhas)
    assert sum(1 for l in linhas if l[:2].isdigit()) == 30
    assert linhas[-1].startswith("Dias úteis: ") and "Pendências: " in linhas[-1]


def test_marcacao_vazia_no_meio_vai_vazia(app):
    app.salvar_dia(date(2026, 4, 1), TipoDia.TRABALHO, {"entrada": "07:45", "saida": "14:45"})
    _, conteudo = app.folha_em_csv(2026, 4)
    assert conteudo.splitlines()[1].startswith("01;Qua;07:45;;;14:45;;;")
