"""UC06 Preparar calendário do ano, e as ações de UC03/UC10 que mexem nele.

Junta a lib (`oficial`), a regra de emenda (`emendas`) e as datas manuais do
repositório. Toda gravação passa pelo `Repositorio`: este módulo não fala SQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from folha_ponto.calendario.emendas import EmendaCandidata, emendas_candidatas
from folha_ponto.calendario.oficial import FONTE, calendario_oficial
from folha_ponto.dados import DataDoCalendario, Origem, Repositorio
from folha_ponto.dominio import DataEspecial, ErroDeValidacao, Natureza
from folha_ponto.dominio.preferencias import Preferencias

FONTE_DA_REGRA = "RN05"


@dataclass(frozen=True)
class CalendarioPreparado:
    ano: int
    feriados: int
    facultativos: int
    emendas_sugeridas: list[EmendaCandidata]
    aviso: str = ""   # UC06 E1


def preparar_ano(repo: Repositorio, ano: int, preferencias: Preferencias | None = None) -> CalendarioPreparado:
    """UC06 (e o "Recalcular calendário" do 1'). Preserva manuais, emendas confirmadas e ocultas."""
    preferencias = preferencias or repo.preferencias()
    # A emenda de 31/12 pode vir de um feriado em 01/01 do ano seguinte (e vice-versa).
    oficial = calendario_oficial([ano - 1, ano, ano + 1], preferencias.uf)
    ja_gravadas = repo.datas_do_periodo(date(ano - 1, 12, 1), date(ano + 1, 1, 31), incluir_ocultas=True)
    ocultas = {(d.data, d.nome) for d in ja_gravadas if d.oculta}

    base = [(d.data, DataEspecial(d.nome, d.natureza)) for d in oficial.datas if (d.data, d.nome) not in ocultas]
    base += [(d.data, d.especial) for d in ja_gravadas if d.origem is Origem.MANUAL and not d.oculta]
    candidatas = [c for c in emendas_candidatas(base, preferencias.facultativo_e_folga) if c.data.year == ano]

    do_ano = [d for d in oficial.datas if d.data.year == ano]
    automaticas = [DataDoCalendario(d.data, d.nome, d.natureza, Origem(d.origem), fonte=oficial.fonte)
                   for d in do_ano]
    automaticas += [DataDoCalendario(c.data, c.nome, Natureza.EMENDA_SUGERIDA, Origem.REGRA_EMENDA,
                                     fonte=f"{FONTE_DA_REGRA} · {FONTE}") for c in candidatas]
    repo.substituir_calendario_automatico(ano, automaticas)

    return CalendarioPreparado(
        ano=ano,
        feriados=sum(1 for d in do_ano if d.natureza is Natureza.FERIADO),
        facultativos=sum(1 for d in do_ano if d.natureza is Natureza.FACULTATIVO),
        emendas_sugeridas=candidatas,
        aviso=oficial.aviso,
    )


def garantir_ano(repo: Repositorio, ano: int, preferencias: Preferencias | None = None) -> CalendarioPreparado | None:
    """UC06 disparado pelo Tempo: abre o app ou navega para um ano ainda não preparado."""
    if ano in repo.anos_com_calendario():
        return None
    return preparar_ano(repo, ano, preferencias)


# ---- UC10 ----------------------------------------------------------------------
NATUREZAS_MANUAIS = (Natureza.FERIADO, Natureza.EMENDA, Natureza.FACULTATIVO)


def cadastrar_data(repo: Repositorio, dia: date, nome: str, natureza: Natureza = Natureza.FERIADO,
                   recorrente: bool = False) -> DataDoCalendario:
    """UC10: feriado municipal (ex.: aniversário de Cubatão) ou emenda dada pela empresa.
    Recalcula o ano, porque um feriado novo pode gerar uma emenda candidata."""
    nome = (nome or "").strip()
    if not nome:
        raise ErroDeValidacao("Informe o nome da data.")
    if natureza not in NATUREZAS_MANUAIS:
        raise ErroDeValidacao("Cadastre um feriado, um ponto facultativo ou uma emenda.")
    data = DataDoCalendario(dia, nome, natureza, Origem.MANUAL, recorrente=recorrente)
    repo.salvar_data_manual(data)
    _recalcular_se_preparado(repo, dia.year)
    return data


def remover_data(repo: Repositorio, dia: date, nome: str) -> bool:
    """UC10 1': só datas manuais são apagadas; as da lib são ocultadas (`ocultar_data`)."""
    removida = repo.apagar_data_manual(dia, nome)
    if removida:
        _recalcular_se_preparado(repo, dia.year)
    return removida


def ocultar_data(repo: Repositorio, dia: date, nome: str, oculta: bool = True) -> bool:
    """UC10 1': ex.: a empresa não dá o ponto facultativo. Recalcula as emendas."""
    alterada = repo.ocultar_data(dia, nome, oculta)
    if alterada:
        _recalcular_se_preparado(repo, dia.year)
    return alterada


# ---- UC03 ----------------------------------------------------------------------
def _sugestao(repo: Repositorio, dia: date) -> DataDoCalendario:
    for d in repo.datas_do_periodo(dia, dia):
        if d.natureza is Natureza.EMENDA_SUGERIDA:
            return d
    raise ErroDeValidacao(f"{dia:%d/%m/%Y} não é uma emenda candidata.")


def confirmar_emenda(repo: Repositorio, dia: date) -> DataDoCalendario:
    """UC03: a empresa deu a emenda. Vira data manual de natureza emenda (= folga, D6)
    e passa a valer como dia não útil (RN07). Mesma chave (data, nome) da sugestão:
    a confirmação a substitui, e o recalcular não a recria."""
    sugestao = _sugestao(repo, dia)
    confirmada = DataDoCalendario(dia, sugestao.nome, Natureza.EMENDA, Origem.MANUAL)
    repo.salvar_data_manual(confirmada)
    return confirmada


def descartar_emenda(repo: Repositorio, dia: date) -> None:
    """UC03 passo 3: a empresa não deu a emenda. A sugestão fica oculta (sobrevive ao recalcular)."""
    sugestao = _sugestao(repo, dia)
    repo.ocultar_data(dia, sugestao.nome)


def _recalcular_se_preparado(repo: Repositorio, ano: int) -> None:
    if ano in repo.anos_com_calendario():
        preparar_ano(repo, ano)


__all__ = ["CalendarioPreparado", "cadastrar_data", "confirmar_emenda", "descartar_emenda",
           "garantir_ano", "ocultar_data", "preparar_ano", "remover_data"]
