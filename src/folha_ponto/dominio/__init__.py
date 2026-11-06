"""Domínio da folha de ponto (subdomínio Core): Python puro, sem banco, sem UI, sem rede."""

from folha_ponto.dominio.dias_especiais import Calendario, DataEspecial, Natureza, SemCalendario
from folha_ponto.dominio.lancamento import JORNADA_PADRAO, Jornada, Lancamento, calcular_horas, calcular_status
from folha_ponto.dominio.marcacoes import ErroDeValidacao, Marcacoes, escrever_horario, ler_horario
from folha_ponto.dominio.mes import LinhaDaFolha, Mes, Pendencia, ResumoDoMes, TipoPendencia
from folha_ponto.dominio.preferencias import Preferencias
from folha_ponto.dominio.registro import bater_ponto, eh_dia_util, eh_fim_de_semana, tipo_sugerido
from folha_ponto.dominio.vocabulario import MARCACOES_NORMAIS, Marcacao, Status, TipoDia

__all__ = [
    "Calendario", "DataEspecial", "Natureza", "SemCalendario",
    "JORNADA_PADRAO", "Jornada", "Lancamento", "calcular_horas", "calcular_status",
    "ErroDeValidacao", "Marcacoes", "escrever_horario", "ler_horario",
    "LinhaDaFolha", "Mes", "Pendencia", "ResumoDoMes", "TipoPendencia", "Preferencias",
    "bater_ponto", "eh_dia_util", "eh_fim_de_semana", "tipo_sugerido",
    "MARCACOES_NORMAIS", "Marcacao", "Status", "TipoDia",
]
