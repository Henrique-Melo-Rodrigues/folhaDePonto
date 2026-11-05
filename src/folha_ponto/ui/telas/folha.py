"""Aba Folha: o mês na ordem da folha de papel, para copiar à mão (UC08, RN10)."""

from __future__ import annotations

import flet as ft

from folha_ponto.dominio import LinhaDaFolha, escrever_horario
from folha_ponto.ui.estilo import DIAS_CURTOS
from folha_ponto.ui.telas.base import Contexto, Tela, faixa, quando_clicar
from folha_ponto.ui.telas.mes import navegacao_do_mes

LARGURA_DIA, LARGURA_HORA = 40, 46


class TelaFolha(Tela):
    def __init__(self, ctx: Contexto) -> None:
        super().__init__(ctx)
        self.copiadas: set[int] = set()     # só visual; reinicia ao trocar de mês (UC08)
        self.ver_mesmo_assim = False
        self._mes_aberto: tuple[int, int] | None = None

    def trocar_de_mes(self) -> None:
        self.atualizar()
        self.ctx.redesenhar()

    def construir(self) -> list[ft.Control]:
        if self._mes_aberto != (self.ctx.ano, self.ctx.mes):
            self._mes_aberto = (self.ctx.ano, self.ctx.mes)
            self.copiadas, self.ver_mesmo_assim = set(), False

        paleta = self.ctx.paleta
        mes = self.servicos.mes(self.ctx.ano, self.ctx.mes)
        controles: list[ft.Control] = [navegacao_do_mes(self.ctx, self.trocar_de_mes)]

        pendencias = mes.pendencias(self.servicos.hoje())   # UC08 passo 1 inclui UC07
        if pendencias and not self.ver_mesmo_assim:
            controles += [
                faixa(f"{len(pendencias)} pendência(s) neste mês.", paleta.aviso_fundo, paleta.aviso_texto),
                ft.Row([ft.FilledButton("Resolver", on_click=quando_clicar(lambda: self.ctx.ir_para("mes"))),
                        ft.TextButton("Ver mesmo assim", on_click=quando_clicar(self.mostrar_mesmo_assim))]),
            ]
            return controles

        controles.append(self._cabecalho())
        controles += [self._linha(linha) for linha in mes.folha()]
        controles.append(ft.Text("Toque numa linha para marcá-la como copiada.", size=12, color=paleta.texto_fraco))
        return controles

    def mostrar_mesmo_assim(self) -> None:
        self.ver_mesmo_assim = True
        self.atualizar()
        self.ctx.redesenhar()

    def alternar_copiada(self, dia: int) -> None:
        self.copiadas ^= {dia}
        self.atualizar()
        self.ctx.redesenhar()

    def _cabecalho(self) -> ft.Control:
        paleta = self.ctx.paleta
        def celula(texto: str, largura: int) -> ft.Text:
            return ft.Text(texto, width=largura, size=11, weight=ft.FontWeight.BOLD, color=paleta.texto_fraco)
        return ft.Row([celula("DIA", LARGURA_DIA)] + [celula(t, LARGURA_HORA) for t in
                       ("M ent", "M saí", "T ent", "T saí", "E ent", "E saí")], spacing=2)

    def _linha(self, linha: LinhaDaFolha) -> ft.Control:
        paleta = self.ctx.paleta
        copiada = linha.dia in self.copiadas
        horarios = [*linha.manha, *linha.tarde, *linha.extra]
        estilo = ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH) if copiada else None
        celulas = [ft.Text(f"{linha.dia:02d} {DIAS_CURTOS[linha.data.weekday()]}", width=LARGURA_DIA, size=13,
                           weight=ft.FontWeight.BOLD, style=estilo)]
        celulas += [ft.Text(escrever_horario(h) or "—", width=LARGURA_HORA, size=13, style=estilo) for h in horarios]
        conteudo: list[ft.Control] = [ft.Row(celulas, spacing=2)]
        if linha.observacao:
            conteudo.append(ft.Text(linha.observacao, size=11, color=paleta.texto_fraco, style=estilo))
        return ft.Container(
            ft.Column(conteudo, spacing=2, tight=True), padding=ft.Padding.symmetric(horizontal=6, vertical=4),
            border_radius=6, opacity=0.45 if copiada else 1.0,
            bgcolor=paleta.neutro_fundo if linha.data.weekday() >= 5 else None,
            on_click=quando_clicar(lambda: self.alternar_copiada(linha.dia)))
