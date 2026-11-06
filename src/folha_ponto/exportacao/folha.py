"""A folha do mês em texto ou CSV (UC08 2'): o mesmo conteúdo da aba Folha,
na ordem do papel (D5, RN10), pronto para o menu Compartilhar."""

from __future__ import annotations

import csv
import io
from datetime import date, time

from folha_ponto.dominio import Mes, escrever_horario

MESES = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
         "Setembro", "Outubro", "Novembro", "Dezembro")
_DIA_CURTO = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
COLUNAS_CSV = ("dia", "dia_da_semana", "manha_entrada", "manha_saida", "tarde_entrada", "tarde_saida",
               "extra_entrada", "extra_saida", "observacao")


def _horarios(linha) -> list[time | None]:
    return [*linha.manha, *linha.tarde, *linha.extra]


def _duracao(d) -> str:
    minutos = round(d.total_seconds() / 60)
    sinal = "-" if minutos < 0 else ""
    return f"{sinal}{abs(minutos) // 60}h{abs(minutos) % 60:02d}"


def folha_em_texto(mes: Mes, hoje: date) -> str:
    """Texto monoespaçado: cabeçalho, uma linha por dia e o resumo."""
    linhas = [f"Folha de ponto — {MESES[mes.mes - 1]} {mes.ano}", "",
              "DIA     MANHÃ         TARDE         EXTRA",
              "        ent   saí     ent   saí     ent   saí"]
    for linha in mes.folha():
        h = [escrever_horario(x) or "  —  " for x in _horarios(linha)]
        texto = f"{linha.dia:02d} {_DIA_CURTO[linha.data.weekday()]}  {h[0]} {h[1]}   {h[2]} {h[3]}   {h[4]} {h[5]}"
        if linha.observacao:
            texto += f"  {linha.observacao}"
        linhas.append(texto.rstrip())
    resumo = mes.resumo(hoje)
    linhas += ["", f"Dias úteis: {resumo.dias_uteis} · Lançados: {resumo.dias_lancados} · "
                   f"Horas: {_duracao(resumo.horas)} · Saldo: {_duracao(resumo.saldo)} · Pendências: {resumo.pendencias}"]
    return "\n".join(linhas) + "\n"


def folha_em_csv(mes: Mes) -> str:
    """CSV com `;` (abre direto no Excel/LibreOffice em português)."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\n")
    escritor.writerow(COLUNAS_CSV)
    for linha in mes.folha():
        escritor.writerow([f"{linha.dia:02d}", _DIA_CURTO[linha.data.weekday()],
                           *(escrever_horario(h) for h in _horarios(linha)), linha.observacao])
    return saida.getvalue()


def nome_do_arquivo(mes: Mes, extensao: str) -> str:
    return f"folha-{mes.ano:04d}-{mes.mes:02d}.{extensao}"
