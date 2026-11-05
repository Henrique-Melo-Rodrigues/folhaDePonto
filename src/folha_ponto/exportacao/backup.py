"""Arquivo de backup (UC09): JSON versionado com tudo o que é do usuário.

Python puro: monta o JSON a partir de um `Instantaneo` e valida o caminho de
volta. Um arquivo inválido não chega ao banco (UC09 E1): `ler_backup` levanta
`ErroDeBackup` antes de qualquer gravação.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time

from folha_ponto import __version__
from folha_ponto.dados import Carimbos, DataDoCalendario, Instantaneo, LancamentoCarimbado, Origem
from folha_ponto.dominio import ErroDeValidacao, Lancamento, Marcacao, Marcacoes, Natureza, TipoDia, ler_horario
from folha_ponto.dominio.lancamento import Jornada
from folha_ponto.dominio.preferencias import Preferencias

FORMATO = "folha-de-ponto-backup"
VERSAO = 1   # mudou o formato? some 1 e ensine `ler_backup` a ler a versão anterior


class ErroDeBackup(ValueError):
    """Arquivo inválido ou de versão desconhecida (UC09 E1)."""


@dataclass(frozen=True)
class Backup:
    """Um backup já lido e validado, pronto para `Repositorio.importar`."""

    dados: Instantaneo
    gerado_em: datetime | None
    versao_do_app: str

    @property
    def dias(self) -> int:
        """UC09 2': "quantos dias serão importados"."""
        return len(self.dados.lancamentos)


def nome_do_arquivo(hoje: date) -> str:
    return f"backup-{hoje.isoformat()}.json"


# ---- escrever ---------------------------------------------------------------------
def gerar_backup(dados: Instantaneo, agora: datetime) -> str:
    p = dados.preferencias
    preferencias = asdict(p) | {"jornada": {k: v.strftime("%H:%M") for k, v in asdict(p.jornada).items()}}
    documento = {
        "formato": FORMATO,
        "versao": VERSAO,
        "gerado_em": agora.isoformat(),
        "app": __version__,
        "lancamentos": [
            {"data": i.lancamento.data.isoformat(), "tipo": i.lancamento.tipo.value,
             **i.lancamento.marcacoes.como_textos(), "observacao": i.lancamento.observacao,
             "criado_em": i.carimbos.criado_em.isoformat(), "atualizado_em": i.carimbos.atualizado_em.isoformat()}
            for i in dados.lancamentos
        ],
        "datas_manuais": [{"data": d.data.isoformat(), "nome": d.nome, "natureza": d.natureza.value,
                           "recorrente": d.recorrente} for d in dados.datas_manuais],
        "datas_ocultas": [{"data": d.data.isoformat(), "nome": d.nome, "natureza": d.natureza.value,
                           "origem": d.origem.value, "fonte": d.fonte} for d in dados.datas_ocultas],
        "preferencias": preferencias,
    }
    return json.dumps(documento, ensure_ascii=False, indent=2)


# ---- ler --------------------------------------------------------------------------
def ler_backup(conteudo: str | bytes) -> Backup:
    try:
        documento = json.loads(conteudo)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ErroDeBackup("O arquivo não é um backup válido (JSON ilegível).") from e
    if not isinstance(documento, dict) or documento.get("formato") != FORMATO:
        raise ErroDeBackup("O arquivo não é um backup da Folha de Ponto.")
    versao = documento.get("versao")
    if versao != VERSAO:
        raise ErroDeBackup(f"Backup na versão {versao!r}; este app lê a versão {VERSAO}. Atualize o app.")

    try:
        lancamentos = tuple(_lancamento(item) for item in _lista(documento, "lancamentos"))
        datas = [l.lancamento.data for l in lancamentos]
        if len(datas) != len(set(datas)):
            raise ErroDeBackup("O backup tem dois lançamentos para a mesma data (RN04).")
        manuais = tuple(DataDoCalendario(date.fromisoformat(d["data"]), _nome(d), Natureza(d["natureza"]),
                                         Origem.MANUAL, recorrente=bool(d.get("recorrente", False)))
                        for d in _lista(documento, "datas_manuais"))
        ocultas = tuple(DataDoCalendario(date.fromisoformat(d["data"]), _nome(d), Natureza(d["natureza"]),
                                         _origem_automatica(d["origem"]), oculta=True, fonte=str(d.get("fonte", "")))
                        for d in _lista(documento, "datas_ocultas"))
        preferencias = _preferencias(documento.get("preferencias") or {})
        gerado_em = datetime.fromisoformat(documento["gerado_em"]) if documento.get("gerado_em") else None
    except ErroDeBackup:
        raise
    except (ErroDeValidacao, KeyError, TypeError, ValueError, AttributeError) as e:
        raise ErroDeBackup(f"Backup com dado inválido: {e}") from e

    return Backup(Instantaneo(lancamentos, manuais, ocultas, preferencias), gerado_em, str(documento.get("app", "")))


def _lista(documento: dict, chave: str) -> list[dict]:
    valor = documento.get(chave, [])
    if not isinstance(valor, list) or not all(isinstance(i, dict) for i in valor):
        raise ErroDeBackup(f"O campo {chave!r} do backup deveria ser uma lista.")
    return valor


def _nome(d: dict) -> str:
    nome = str(d["nome"]).strip()
    if not nome:
        raise ErroDeBackup("Data do calendário sem nome.")
    return nome


def _origem_automatica(valor: str) -> Origem:
    origem = Origem(valor)
    if not origem.automatica:
        raise ErroDeBackup("Data oculta com origem manual.")
    return origem


def _carimbo(texto: str) -> datetime:
    momento = datetime.fromisoformat(texto)
    if momento.tzinfo is None:
        raise ErroDeBackup("Carimbo de data/hora sem fuso horário.")
    return momento


def _lancamento(item: dict) -> LancamentoCarimbado:
    lancamento = Lancamento(
        data=date.fromisoformat(item["data"]),
        tipo=TipoDia(item["tipo"]),
        marcacoes=Marcacoes.de_textos({m.value: item.get(m.value) for m in Marcacao}),
        observacao=str(item.get("observacao", "")),
    )
    return LancamentoCarimbado(lancamento, Carimbos(_carimbo(item["criado_em"]), _carimbo(item["atualizado_em"])))


def _preferencias(valores: dict) -> Preferencias:
    if not isinstance(valores, dict):
        raise ErroDeBackup("Preferências inválidas no backup.")
    conhecidas = {k: v for k, v in valores.items() if k in Preferencias.__dataclass_fields__}
    if "jornada" in conhecidas:
        horarios: dict[str, time | None] = {k: ler_horario(v) for k, v in conhecidas["jornada"].items()}
        if set(horarios) != set(Jornada.__dataclass_fields__) or None in horarios.values():
            raise ErroDeBackup("A jornada do backup precisa dos quatro horários.")
        Marcacoes(**horarios)  # RN02: na ordem do dia
        conhecidas["jornada"] = Jornada(**horarios)
    return Preferencias(**conhecidas)
