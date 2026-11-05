"""Aba Mês: grade do calendário com status, feriados e emendas (UC05), resumo (RN08)
e pendências (UC07)."""

from __future__ import annotations

import calendar
from datetime import date

import flet as ft

from folha_ponto.dominio import Mes, escrever_horario
from folha_ponto.ui.estilo import DIAS_CURTOS, mes_vizinho, nome_do_mes
from folha_ponto.ui.servicos import escrever_duracao
from folha_ponto.ui.telas.base import Contexto, Tela, quando_clicar


def navegacao_do_mes(ctx: Contexto, ao_trocar) -> ft.Row:
    """‹ Abril 2026 › — compartilhada por Mês e Folha (o mês aberto é o mesmo nas duas)."""
    def trocar(passo: int) -> None:
        ctx.ano, ctx.mes = mes_vizinho(ctx.ano, ctx.mes, passo)
        ao_trocar()

    return ft.Row([
        ft.IconButton(ft.Icons.CHEVRON_LEFT, tooltip="Mês anterior", on_click=quando_clicar(lambda: trocar(-1))),
        ft.Text(nome_do_mes(ctx.ano, ctx.mes), size=20, weight=ft.FontWeight.BOLD),
        ft.IconButton(ft.Icons.CHEVRON_RIGHT, tooltip="Próximo mês", on_click=quando_clicar(lambda: trocar(1))),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


class TelaMes(Tela):
    def trocar_de_mes(self) -> None:
        self.atualizar()
        self.ctx.redesenhar()

    def construir(self) -> list[ft.Control]:
        mes = self.servicos.mes(self.ctx.ano, self.ctx.mes)
        hoje = self.servicos.hoje()
        paleta = self.ctx.paleta
        controles: list[ft.Control] = [navegacao_do_mes(self.ctx, self.trocar_de_mes)]
        controles.append(ft.Row([ft.Text(d, expand=True, text_align=ft.TextAlign.CENTER, color=paleta.texto_fraco)
                                 for d in DIAS_CURTOS], spacing=4))
        for semana in calendar.Calendar(firstweekday=0).monthdatescalendar(mes.ano, mes.mes):
            controles.append(ft.Row([self._celula(mes, dia, hoje) for dia in semana], spacing=4))

        resumo = mes.resumo(hoje)
        controles.append(ft.Container(ft.Column([
            ft.Text(f"Dias úteis: {resumo.dias_uteis} · Lançados: {resumo.dias_lancados}"),
            ft.Text(f"Horas: {escrever_duracao(resumo.horas) or '0h00'} · Saldo: {escrever_duracao(resumo.saldo) or '0h00'}"),
            ft.Text(f"Pendências: {resumo.pendencias}",
                    color=paleta.aviso_texto if resumo.pendencias else paleta.ok_texto, weight=ft.FontWeight.BOLD),
        ], spacing=4, tight=True), padding=12, border_radius=10, bgcolor=paleta.superficie,
            border=ft.Border.all(1, paleta.borda)))

        for pendencia in mes.pendencias(hoje):  # UC07: cada item abre o dia (UC02)
            controles.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.WARNING_AMBER, color=paleta.aviso_texto),
                title=ft.Text(f"{pendencia.data:%d/%m} · {pendencia.tipo.rotulo}"),
                subtitle=ft.Text(pendencia.descricao), dense=True,
                on_click=quando_clicar(lambda d=pendencia.data: self.ctx.abrir_dia(d))))

        controles.append(ft.Row([ft.FilledButton("Ver folha para cópia", icon=ft.Icons.TABLE_ROWS, expand=True,
                                                 on_click=quando_clicar(lambda: self.ctx.ir_para("folha")))]))
        return controles

    def _celula(self, mes: Mes, dia: date, hoje: date) -> ft.Control:
        paleta = self.ctx.paleta
        if dia.month != mes.mes:
            return ft.Container(expand=True, height=64)
        lancamento = mes.lancamentos.get(dia)
        especial = mes.especial(dia)
        linhas: list[ft.Control] = [ft.Text(str(dia.day), weight=ft.FontWeight.BOLD, size=13,
                                            color=paleta.primaria if dia == hoje else paleta.texto)]
        if lancamento is not None and lancamento.tipo.trabalhado:
            m = lancamento.marcacoes
            linhas += [ft.Text(escrever_horario(m.entrada) or "--:--", size=10),
                       ft.Text(escrever_horario(m.saida) or "--:--", size=10)]
        elif lancamento is not None:
            linhas.append(ft.Text(lancamento.tipo.rotulo_curto, size=10))
        if especial is not None:
            linhas.append(ft.Text(especial.nome, size=9, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                  color=paleta.cor_da_natureza(especial.natureza)))
        return ft.Container(
            ft.Column(linhas, spacing=0, tight=True), expand=True, height=64, padding=3, border_radius=8,
            bgcolor=paleta.fundo_do_status(lancamento.status if lancamento else None),
            border=ft.Border.all(2 if especial else 1, paleta.cor_da_natureza(especial.natureza if especial else None)),
            tooltip=especial.nome if especial else None,
            on_click=quando_clicar(lambda: self.ctx.abrir_dia(dia)))
