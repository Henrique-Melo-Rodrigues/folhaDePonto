# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Gera o modelo ArchiMate (Archi 5.x) da Folha de Ponto Pessoal v2.

Mesmo método do projeto Magalu (gera_fase_b_v2.py): TOGAF ADM em pastas
(Preliminar, A, B, C, D, E-F), baseline -> target -> gap analysis, e cada
relação conferida contra a tabela oficial do ArchiMate 3.2 que vem no Archi.

Uso (só biblioteca padrão):
    uv run docs/arquitetura/gera_modelo.py [saida.archimate] [relationships.xml]
"""

from __future__ import annotations

import glob
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
DST = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "folha-de-ponto.archimate"
RELS = sys.argv[2] if len(sys.argv) > 2 else next(
    iter(sorted(glob.glob("/opt/archi/plugins/com.archimatetool.model_*/model/relationships.xml"))), None
)
if not RELS:
    raise SystemExit("relationships.xml do Archi não encontrado; passe o caminho como 2º argumento.")

XSI = "http://www.w3.org/2001/XMLSchema-instance"
ARCHI = "http://www.archimatetool.com/archimate"
ET.register_namespace("xsi", XSI)
ET.register_namespace("archimate", ARCHI)
T = f"{{{XSI}}}type"

LET = {"Access": "a", "Composition": "c", "Flow": "f", "Aggregation": "g", "Assignment": "i",
       "Influence": "n", "Association": "o", "Realization": "r", "Specialization": "s",
       "Triggering": "t", "Serving": "v"}
RULES = {(s.get("concept"), t.get("concept")): t.get("relations")
         for s in ET.parse(RELS).getroot().findall("source") for t in s.findall("target")}
ACCESS = {"w": "0", "r": "1", "rw": "3"}


def nid() -> str:
    return "id-" + uuid.uuid4().hex


# ----------------------------------------------------------------- modelo base
root = ET.Element(f"{{{ARCHI}}}model", {"name": "Folha de Ponto Pessoal v2 (app offline)",
                                         "id": nid(), "version": "5.0.0"})
TOP = {}
for name, ftype in [("Strategy", "strategy"), ("Business", "business"), ("Application", "application"),
                    ("Technology & Physical", "technology"), ("Motivation", "motivation"),
                    ("Implementation & Migration", "implementation_migration"), ("Other", "other"),
                    ("Relations", "relations"), ("Views", "diagrams")]:
    TOP[ftype] = ET.SubElement(root, "folder", {"name": name, "id": nid(), "type": ftype})

FOLDERS: dict[tuple[str, str], ET.Element] = {}


def folder(ftype: str, name: str) -> ET.Element:
    if (ftype, name) not in FOLDERS:
        FOLDERS[(ftype, name)] = ET.SubElement(TOP[ftype], "folder", {"name": name, "id": nid()})
    return FOLDERS[(ftype, name)]


E: dict[str, str] = {}       # chave curta -> id
KIND: dict[str, str] = {}    # id -> tipo ArchiMate
RELS_ALL: list[tuple[str, str, str, str]] = []  # (id, tipo, origem, destino)

LAYER = {"Stakeholder": "motivation", "Driver": "motivation", "Assessment": "motivation", "Goal": "motivation",
         "Outcome": "motivation", "Principle": "motivation", "Requirement": "motivation",
         "Constraint": "motivation", "Capability": "strategy", "CourseOfAction": "strategy",
         "BusinessActor": "business", "BusinessRole": "business", "BusinessProcess": "business",
         "BusinessEvent": "business", "BusinessObject": "business",
         "ApplicationComponent": "application", "ApplicationService": "application",
         "ApplicationInterface": "application", "DataObject": "application",
         "Device": "technology", "Node": "technology", "SystemSoftware": "technology",
         "TechnologyService": "technology", "TechnologyProcess": "technology", "Artifact": "technology",
         "CommunicationNetwork": "technology", "WorkPackage": "implementation_migration",
         "Deliverable": "implementation_migration", "Plateau": "implementation_migration",
         "Gap": "implementation_migration"}


def el(key: str, kind: str, name: str, doc: str, sub: str | None = None, **props: str) -> str:
    parent = folder(LAYER[kind], sub) if sub else TOP[LAYER[kind]]
    e = ET.SubElement(parent, "element", {T: f"archimate:{kind}", "name": name, "id": nid()})
    ET.SubElement(e, "documentation").text = doc
    for k, v in props.items():
        ET.SubElement(e, "property", {"key": k.replace("_", " "), "value": v})
    E[key] = e.get("id")
    KIND[E[key]] = kind
    return E[key]


def rel(kind: str, src: str, tgt: str, sub: str, name: str | None = None, access: str | None = None) -> str:
    s, t = E[src], E[tgt]
    if LET[kind] not in RULES.get((KIND[s], KIND[t]), ""):
        raise SystemExit(f"RELAÇÃO INVÁLIDA no ArchiMate 3.2: {kind} {KIND[s]}({src}) -> {KIND[t]}({tgt})")
    a = {T: f"archimate:{kind}Relationship", "id": nid(), "source": s, "target": t}
    if name:
        a["name"] = name
    if kind == "Access":
        a["accessType"] = ACCESS[access or "w"]
    ET.SubElement(folder("relations", sub), "element", a)
    RELS_ALL.append((a["id"], kind, s, t))
    return a["id"]


def rels(kind: str, pairs: list[tuple[str, str]], sub: str, **kw) -> None:
    for s, t in pairs:
        rel(kind, s, t, sub, **kw)


# ======================================================================
# PRELIMINAR — princípios de arquitetura
# ======================================================================
P = "0. Preliminar"
el("P1", "Principle", "Offline primeiro (local-first)",
   "O app funciona sem rede, em qualquer lugar. Nenhum caminho de uso depende de servidor ou internet.", P)
el("P2", "Principle", "Simplicidade antes de generalidade",
   "Uma única pilha e um único banco. Só se adiciona peça quando um caso de uso precisa dela.", P)
el("P3", "Principle", "Uma linguagem: Python com uv",
   "Regras, persistência, calendário e interface em Python. Dependências fixadas em pyproject.toml + uv.lock.", P)
el("P4", "Principle", "Regras testáveis sem interface",
   "Domínio e calendário em Python puro, testados com pytest no PC, sem emulador.", P)
el("P5", "Principle", "Dados do usuário no aparelho e sob controle dele",
   "Os lançamentos ficam no SQLite do app. O backup é um arquivo que o próprio usuário guarda.", P)

# ======================================================================
# FASE A — visão: stakeholders, drivers, objetivos, requisitos
# ======================================================================
A = "A. Vision"
el("S_trab", "Stakeholder", "Trabalhador (aprendiz)",
   "Dono da folha de ponto. Anota os horários todo dia e preenche a folha oficial no fim do mês.", A)
el("S_emp", "Stakeholder", "Empresa (RH / supervisor)",
   "Recebe a folha de ponto preenchida e assinada no fim do mês.", A)
el("D1", "Driver", "Horários espalhados no WhatsApp",
   "Entrada, almoço, volta e saída ficam em mensagens soltas ao longo de semanas.", A)
el("D2", "Driver", "Rede da empresa bloqueia APIs externas",
   "No trabalho não dá para depender de servidor em casa nem de API na internet.", A)
el("D3", "Driver", "Feriados e emendas esquecidos",
   "No fim do mês é preciso lembrar quais dias foram feriado, ponto facultativo ou emenda.", A)
el("D4", "Driver", "Complexidade acidental do repositório",
   "Django, React, Flutter, orquestrador multi-CLI e restos de MongoDB convivem para um app de uma pessoa.", A)
el("D5", "Driver", "Folha oficial correta e no prazo",
   "A empresa precisa da folha de papel preenchida, sem lacunas, no fim de cada mês.", A)
el("AS_1", "Assessment", "Fim do mês exige garimpar conversas",
   "Juntar os horários vira um trabalho à parte, repetitivo e sujeito a erro (README).", A)
el("AS_2", "Assessment", "App atual depende de servidor na rede de casa",
   "O web-app roda num celular velho com Termux; fora de casa, não abre.", A)
el("AS_3", "Assessment", "Regras duplicadas em Python e Dart",
   "calculate_status existe em services.py e em status.dart, mantidos juntos por vetores golden.", A)
el("AS_4", "Assessment", "Sem backup dos dados",
   "Perder ou trocar o celular perde o histórico (consequência registrada no ADR-001).", A)
el("G1", "Goal", "Preencher a folha do mês sem garimpo",
   "Ter tudo do mês num só lugar, na ordem da folha de papel.", A)
el("G2", "Goal", "Registrar o ponto na hora, em segundos",
   "A anotação acontece no momento do evento, com um toque.", A)
el("G3", "Goal", "Funcionar em qualquer rede, sem internet", "Inclusive dentro da rede da empresa.", A)
el("G4", "Goal", "Manter o projeto simples de evoluir",
   "Uma pilha, poucos arquivos, testes rápidos. Fácil de estudar e de mudar.", A)
el("G5", "Goal", "Não perder o histórico", "O usuário consegue guardar e restaurar os próprios dados.", A)
el("O1", "Outcome", "Folha copiada numa só sessão", "Sem abrir o WhatsApp nem consultar outro calendário.", A)
el("O2", "Outcome", "Nenhum dia útil esquecido", "O app aponta todo dia útil sem lançamento ou incompleto.", A)
el("O3", "Outcome", "Ponto batido no momento em que acontece", "Em até 2 toques a partir do ícone do app.", A)
el("R1", "Requirement", "Bater o ponto em até 2 toques", "UC01, RNF04.", A, caso_de_uso="UC01")
el("R2", "Requirement", "Sugerir feriados e emendas automaticamente",
   "Nacionais e de SP pela lib holidays; Cubatão e emendas da empresa cadastrados. Emenda = folga.", A,
   caso_de_uso="UC03, UC06, UC10")
el("R3", "Requirement", "Listar as pendências do mês",
   "Dia útil sem lançamento, lançamento incompleto, emenda a confirmar.", A, caso_de_uso="UC07")
el("R4", "Requirement", "Mostrar o mês na ordem da folha de papel",
   "DIA · Manhã E/S · Tarde E/S · Extra E/S · observação, dias 01 a 31 corridos.", A, caso_de_uso="UC08")
el("R5", "Requirement", "Registrar hora extra", "Par de marcações Extra (entrada/saída), como na folha oficial.", A,
   caso_de_uso="UC01, UC02")
el("R6", "Requirement", "Backup e restauração por arquivo", "JSON versionado, mesclar ou substituir.", A,
   caso_de_uso="UC09")
el("C1", "Constraint", "APK sem permissão de internet", "RNF01. Um teste reprova qualquer import de rede.", A)
el("C2", "Constraint", "Python ≥ 3.12 gerenciado com uv", "RNF02. Decisão do usuário.", A)
el("C3", "Constraint", "Folha oficial em papel, preenchida à mão",
   "O app não substitui a folha: ele organiza o que vai ser copiado para ela.", A)

rels("Association", [("S_trab", "D1"), ("S_trab", "D2"), ("S_trab", "D3"), ("S_trab", "D4"), ("S_emp", "D5"),
                     ("D1", "AS_1"), ("D3", "AS_1"), ("D2", "AS_2"), ("D4", "AS_3"), ("D4", "AS_4"),
                     ("C3", "R4")], A)
rels("Influence", [("AS_1", "G1"), ("AS_2", "G3"), ("AS_3", "G4"), ("AS_4", "G5"), ("D5", "G1"),
                   ("D1", "G2")], A)
rels("Realization", [("O1", "G1"), ("O2", "G1"), ("O3", "G2"),
                     ("R1", "O3"), ("R2", "O2"), ("R3", "O2"), ("R4", "O1"), ("R5", "O1"), ("R6", "G5"),
                     ("C1", "G3"), ("C2", "G4"),
                     ("C1", "P1"), ("C2", "P3"),
                     ("P1", "G3"), ("P2", "G4"), ("P3", "G4"), ("P4", "G4"), ("P5", "G5")], A)

# estratégia
el("COA", "CourseOfAction", "Reescrever como app Python offline no celular",
   "Uma pilha só (Python + uv + SQLite + Flet), rodando no aparelho do Trabalhador.", A)
el("CAP1", "Capability", "Registro de jornada", "Anotar marcações e classificar o dia.", A,
   subdominio_DDD="Core")
el("CAP2", "Capability", "Calendário de feriados e emendas",
   "Feriados oficiais (lib pronta) + emendas e datas de Cubatão (sob medida).", A,
   subdominio_DDD="Generic (lib holidays) + Supporting (emendas, municipais)")
el("CAP3", "Capability", "Fechamento da folha do mês", "Conferir pendências e copiar a folha.", A,
   subdominio_DDD="Core")
el("CAP4", "Capability", "Proteção dos dados", "Backup e restauração.", A, subdominio_DDD="Supporting")
rels("Realization", [("COA", "G3"), ("COA", "G4"), ("CAP1", "COA"), ("CAP2", "COA"), ("CAP3", "COA"),
                     ("CAP4", "COA"), ("CAP1", "O3"), ("CAP2", "O2"), ("CAP3", "O1"), ("CAP4", "G5")], A)

# ======================================================================
# FASE B — negócio
# ======================================================================
B, BB, BT = "B. Business", "B. 2 Baseline", "B. 3 Target"
el("A_trab", "BusinessActor", "Trabalhador", "Aprendiz que registra o próprio ponto. Único usuário do app.", B)
el("A_emp", "BusinessActor", "Empresa", "Empregadora. Recebe a folha de ponto assinada.", B)
el("RO_dono", "BusinessRole", "Responsável pelo ponto", "Anota, confere e preenche a própria folha.", B)
el("RO_rec", "BusinessRole", "Recebedor da folha", "Recebe e arquiva a folha do mês.", B)
el("EV_mark", "BusinessEvent", "Chegada, almoço ou saída", "Cada um dos momentos que geram uma marcação.", B)
el("EV_fim", "BusinessEvent", "Fim do mês", "Hora de preencher e entregar a folha oficial.", B)
el("BO_folha", "BusinessObject", "Folha de ponto oficial (papel)",
   "Uma linha por dia (01–31) com Manhã, Tarde e Extra (entrada/saída) e assinatura. Jornada 07:45–12:00 e 13:00–14:45.", B)
el("B5", "BusinessProcess", "Entregar a folha assinada", "Igual na baseline e no target (keep).", B)
rels("Assignment", [("A_trab", "RO_dono"), ("A_emp", "RO_rec"), ("RO_dono", "B5")], B)
rel("Serving", "B5", "RO_rec", B)
rel("Access", "B5", "BO_folha", B, access="r")

el("BO_whats", "BusinessObject", "Mensagens com horários (WhatsApp)", "Anotações soltas, sem estrutura.", BB)
el("BO_calm", "BusinessObject", "Calendário de cabeça / internet", "Onde se descobre, no fim do mês, o que foi feriado.", BB)
el("B1", "BusinessProcess", "B1 Anotar horário no WhatsApp", "Mensagem para si mesmo a cada marcação.", BB)
el("B2", "BusinessProcess", "B2 Rolar as conversas do mês", "Garimpar as mensagens, dia por dia.", BB)
el("B3", "BusinessProcess", "B3 Descobrir feriados e emendas", "Lembrar ou pesquisar quais dias não eram úteis.", BB)
el("B4", "BusinessProcess", "B4 Preencher a folha à mão", "Copiar o que foi garimpado para o papel.", BB)
rels("Assignment", [("RO_dono", k) for k in ("B1", "B2", "B3", "B4")], BB)
rels("Triggering", [("EV_mark", "B1"), ("EV_fim", "B2"), ("B2", "B3"), ("B3", "B4"), ("B4", "B5")], BB)
rel("Access", "B1", "BO_whats", BB, access="w")
rel("Access", "B2", "BO_whats", BB, access="r")
rel("Access", "B3", "BO_calm", BB, access="r")
rel("Access", "B4", "BO_folha", BB, access="w")

el("BO_reg", "BusinessObject", "Registro do dia",
   "Data, tipo do dia, marcações Manhã/Tarde/Extra, observação e status (completo, incompleto, não trabalhado).", BT)
el("T1", "BusinessProcess", "T1 Bater o ponto no app", "Um toque grava a hora na próxima marcação vazia.", BT,
   caso_de_uso="UC01, UC02, UC04")
el("T2", "BusinessProcess", "T2 Confirmar feriados e emendas sugeridos",
   "O app sugere; o Trabalhador confirma. Emenda confirmada = folga.", BT, caso_de_uso="UC03, UC10")
el("T3", "BusinessProcess", "T3 Resolver as pendências do mês",
   "Completar os dias úteis sem lançamento ou incompletos.", BT, caso_de_uso="UC05, UC07")
el("T4", "BusinessProcess", "T4 Copiar a folha pela tela Folha",
   "Uma linha por dia, na ordem do papel. Marca cada linha copiada.", BT, caso_de_uso="UC08")
el("T6", "BusinessProcess", "T6 Guardar o backup do mês", "Gerar o arquivo e guardá-lo fora do celular.", BT,
   caso_de_uso="UC09")
rels("Assignment", [("RO_dono", k) for k in ("T1", "T2", "T3", "T4", "T6")], BT)
rels("Triggering", [("EV_mark", "T1"), ("EV_fim", "T3"), ("T3", "T4"), ("T4", "B5"), ("T4", "T6")], BT)
rel("Flow", "T2", "T3", BT)  # fluxo: os dias já classificados
rel("Access", "T1", "BO_reg", BT, access="w")
rel("Access", "T2", "BO_reg", BT, access="w")
rel("Access", "T3", "BO_reg", BT, access="rw")
rel("Access", "T4", "BO_reg", BT, access="r")
rel("Access", "T4", "BO_folha", BT, access="w")
rels("Realization", [("T1", "R1"), ("T1", "R5"), ("T2", "R2"), ("T3", "R3"), ("T4", "R4"), ("T6", "R6"),
                     ("T1", "CAP1"), ("T2", "CAP2"), ("T3", "CAP3"), ("T4", "CAP3"), ("T6", "CAP4")], BT)

# ======================================================================
# FASE C — sistemas de informação (aplicações + dados)
# ======================================================================
CB, CT, CD = "C. 2 Baseline", "C. 3 Target", "C. Dados"
el("AB1", "ApplicationComponent", "API Django + DRF", "src/backend: views → serializers → services → repositories, X-Api-Key.", CB)
el("AB2", "ApplicationComponent", "Web React/Vite", "src/web: abas Hoje/Mês, calendário, tela de chave de API.", CB)
el("AB3", "ApplicationComponent", "App Flutter (sqflite)", "src/mobile: offline, regras portadas para Dart, adapter HTTP opcional.", CB)
el("AB4", "ApplicationComponent", "Orquestrador multi-CLI", "orchestrator.sh (2 cópias): Claude Code builder + Antigravity auditor, agents/, skills/.", CB)
el("AB5", "ApplicationComponent", "Gerador de contratos (Py/TS/Dart)", "contracts/generate.py escreve 3 alvos a partir de time_record.json.", CB)
el("DB_srv", "DataObject", "db.sqlite3 do servidor", "Banco do Django, no celular-servidor.", CB)
el("DB_fl", "DataObject", "folha_de_ponto.db do Flutter", "Banco independente do app Flutter, sem sync.", CB)
rels("Serving", [("AB1", "AB2"), ("AB5", "AB1"), ("AB5", "AB2"), ("AB5", "AB3")], CB)
rel("Access", "AB1", "DB_srv", CB, access="rw")
rel("Access", "AB3", "DB_fl", CB, access="rw")

el("AC_app", "ApplicationComponent", "App Folha de Ponto (pacote folha_ponto)",
   "Um único pacote Python. Roda no celular (APK Flet) e no PC (uv run).", CT)
el("AC_ui", "ApplicationComponent", "Interface (Flet)", "servicos.py orquestra os casos de uso sem Flet (testável); telas/ Hoje, Mês, Folha, Ajustes e o formulário do dia são finas e recebem um Contexto, não a Page.", CT,
   modulo="folha_ponto/ui/", subdominio_DDD="Generic (framework Flet)")
el("AC_dom", "ApplicationComponent", "Domínio: regras do dia",
   "Status, validação HH:MM e ordem das marcações, horas e saldo, pendências e folha do mês. Python puro.", CT,
   modulo="folha_ponto/dominio/", subdominio_DDD="Core")
el("AC_cal", "ApplicationComponent", "Calendário: feriados e emendas",
   "Gera o ano pela lib holidays (BR/UF, public + optional; UF desconhecida cai nos nacionais), aplica a regra de emenda (RN05, inclusive na virada do ano) sobre feriados, facultativos e datas manuais, e grava pelo Repositório. Confirma/descarta emendas (UC03) e cadastra datas manuais (UC10).", CT,
   modulo="folha_ponto/calendario/", subdominio_DDD="Supporting")
el("AC_repo", "ApplicationComponent", "Repositório SQLite",
   "sqlite3 da stdlib, migrações por PRAGMA user_version, transações atômicas e trava para as threads do Flet. Único que fala SQL. Implementa a porta Calendario.", CT,
   modulo="folha_ponto/dados/", subdominio_DDD="Generic")
el("AC_bkp", "ApplicationComponent", "Exportação e backup", "Python puro: folha em texto/CSV (;) na ordem do papel; backup JSON versionado (formato + versão) validado antes de gravar. A restauração (substituir ou mesclar pelo updated_at) é uma transação única do Repositório.", CT,
   modulo="folha_ponto/exportacao/", subdominio_DDD="Supporting")
el("AC_lib", "ApplicationComponent", "Biblioteca holidays (Calendário oficial do Brasil)",
   "Dependência open source, offline. Ator secundário do UC06.", CT, subdominio_DDD="Generic")
el("AI_tel", "ApplicationInterface", "Telas Hoje · Mês · Folha · Ajustes", "O que o Trabalhador toca.", CT)
SERV = [("AS1", "Registrar marcação", "UC01, UC02, UC04", "AC_dom", "T1"),
        ("AS2", "Consultar mês", "UC05", "AC_dom", "T3"),
        ("AS3", "Sugerir feriados e emendas", "UC03, UC06, UC10", "AC_cal", "T2"),
        ("AS4", "Listar pendências do mês", "UC07", "AC_dom", "T3"),
        ("AS5", "Gerar folha para cópia", "UC08", "AC_dom", "T4"),
        ("AS6", "Backup e restauração", "UC09", "AC_bkp", "T6"),
        ("AS7", "Configurar preferências", "UC11", "AC_repo", "T2")]
for key, name, uc, comp, _ in SERV:
    el(key, "ApplicationService", name, f"Serviço que atende {uc}.", CT, caso_de_uso=uc)
rels("Composition", [("AC_app", k) for k in ("AC_ui", "AC_dom", "AC_cal", "AC_repo", "AC_bkp")] +
     [("AC_ui", "AI_tel")], CT)
rels("Realization", [(comp, key) for key, _, _, comp, _ in SERV], CT)
rels("Serving", [(key, proc) for key, *_, proc in SERV] +
     [("AC_lib", "AC_cal"), ("AC_cal", "AC_dom"), ("AC_repo", "AC_dom"), ("AC_repo", "AC_bkp"),
      ("AC_dom", "AC_bkp"), ("AC_dom", "AC_ui"), ("AC_cal", "AC_ui")], CT)
rels("Assignment", [("AI_tel", key) for key, *_ in SERV], CT)

el("DO_reg", "DataObject", "Lançamento do dia (tabela lancamentos)",
   "data (única), tipo, entrada, saida_almoco, volta_almoco, saida, entrada_extra, saida_extra, observacao, criado_em, atualizado_em.", CD)
el("DO_cal", "DataObject", "Data especial (tabela datas_especiais)",
   "data, nome, natureza (feriado, facultativo, emenda, emenda_sugerida), origem (nacional, estadual, facultativo, regra_emenda, manual), recorrente, oculta, fonte (versão da lib).", CD)
el("DO_pref", "DataObject", "Preferências (tabela preferencias)", "UF, município, jornada padrão, facultativo conta como folga (padrão: sim), tema.", CD)
el("DO_ctr", "DataObject", "Vocabulário do domínio (vocabulario.py)", "Enums TipoDia, Status e Marcacao: fonte única dos termos. Sucede o contracts/time_record.json da v1.", CD)
el("DO_bkp", "DataObject", "Arquivo de backup (JSON)", "Versionado; lançamentos, datas manuais, emendas confirmadas, preferências.", CD)
el("DO_folha", "DataObject", "Folha do mês (texto/CSV)", "Mesma ordem de colunas do papel.", CD)
rel("Realization", "DO_reg", "BO_reg", CD)
rel("Association", "DO_folha", "BO_folha", CD, name="copiada para")
for svc, dob, mode in [("AS1", "DO_reg", "rw"), ("AS2", "DO_reg", "r"), ("AS2", "DO_cal", "r"),
                       ("AS3", "DO_cal", "rw"), ("AS4", "DO_reg", "r"), ("AS4", "DO_cal", "r"),
                       ("AS5", "DO_reg", "r"), ("AS5", "DO_folha", "w"), ("AS6", "DO_bkp", "rw"),
                       ("AS6", "DO_reg", "rw"), ("AS7", "DO_pref", "rw")]:
    rel("Access", svc, dob, CD, access=mode)
rel("Access", "AC_dom", "DO_ctr", CD, access="r")
rels("Realization", [("AC_dom", "R1"), ("AC_dom", "R3"), ("AC_dom", "R4"), ("AC_dom", "R5"),
                     ("AC_cal", "R2"), ("AC_bkp", "R6")], CT)

# ======================================================================
# FASE D — tecnologia
# ======================================================================
DB_, DT = "D. 2 Baseline", "D. 3 Target"
el("TB_old", "Device", "Celular velho (Termux + sshd)", "Servidor Django na Wi-Fi de casa, porta 8000. Sai do projeto.", DB_)
el("TB_pc", "Node", "PC na rede de casa (WSL2)", "Build do frontend e deploy por SSH (scripts/deploy-celular.sh).", DB_)
el("TB_net", "CommunicationNetwork", "Wi-Fi de casa", "Única rede onde o app atual funciona.", DB_)
el("TB_dock", "SystemSoftware", "Docker + MongoDB + Caddy", "Restos do plano original. Nunca usados pelo código atual.", DB_)
el("TB_ci", "SystemSoftware", "GitHub Actions (Django, Flutter, contratos)", "3 workflows.", DB_)
rels("Serving", [("TB_old", "AB1"), ("TB_old", "AB2"), ("TB_pc", "AB4")], DB_)
rels("Association", [("TB_net", "TB_old"), ("TB_net", "TB_pc")], DB_)

el("TD", "Device", "Celular Android do Trabalhador", "O mesmo aparelho que vai no bolso. Nada roda fora dele.", DT)
el("SS_and", "SystemSoftware", "Android", "Sem permissão INTERNET no manifest.", DT)
el("SS_py", "SystemSoftware", "Python embarcado (Flet)", "Runtime Python empacotado no APK pelo flet build.", DT)
el("SS_sql", "SystemSoftware", "SQLite (sqlite3 da stdlib)", "Banco embutido, arquivo único.", DT)
el("TS_sto", "TechnologyService", "Armazenamento privado do app", "Diretório de dados do app, apagado só na desinstalação.", DT)
el("TS_sha", "TechnologyService", "Compartilhamento do Android", "Menu Compartilhar: salvar, WhatsApp, e-mail, Drive.", DT)
el("ART_apk", "Artifact", "folha-de-ponto.apk", "Gerado por `uv run flet build apk` no CI (.github/workflows/ci.yml); sem a permissão INTERNET (RNF01), conferido com aapt2.", DT)
el("ART_db", "Artifact", "folha_de_ponto.db", "Arquivo SQLite com lancamentos, datas_especiais e preferencias. Pasta: FLET_APP_STORAGE_DATA.", DT)
el("ART_bkp", "Artifact", "backup-AAAA-MM-DD.json", "Arquivo de backup que o usuário guarda fora do celular.", DT)
el("ND_pc", "Node", "PC de desenvolvimento", "Onde se programa, testa e gera o APK.", DT)
el("SS_uv", "SystemSoftware", "uv + Python 3.12", "uv sync, uv run, uv.lock.", DT)
el("SS_test", "SystemSoftware", "pytest", "Testes do domínio, do calendário e do SQLite, sem emulador.", DT)
el("SS_ci", "SystemSoftware", "GitHub Actions (pytest + build APK)", "Um workflow só.", DT)
el("ART_src", "Artifact", "Pacote folha_ponto (pyproject.toml + uv.lock)", "Código-fonte versionado no git.", DT)
el("TP_bld", "TechnologyProcess", "Gerar o APK", "flet build apk a partir do pacote.", DT)
rels("Composition", [("TD", "SS_and"), ("TD", "SS_py"), ("TD", "SS_sql"), ("ND_pc", "SS_uv"),
                     ("ND_pc", "SS_test")], DT)
rels("Assignment", [("TD", "ART_apk"), ("TD", "ART_db"), ("ND_pc", "ART_src"), ("SS_uv", "TP_bld"),
                    ("SS_ci", "TP_bld")], DT)
rels("Realization", [("SS_and", "TS_sto"), ("SS_and", "TS_sha"), ("ART_apk", "AC_app"), ("ART_db", "DO_reg"),
                     ("ART_db", "DO_cal"), ("ART_db", "DO_pref"), ("ART_bkp", "DO_bkp")], DT)
rels("Serving", [("SS_py", "AC_app"), ("SS_sql", "AC_repo"), ("TS_sto", "AC_repo"), ("TS_sha", "AC_bkp"),
                 ("SS_test", "AC_app")], DT)
rel("Access", "TP_bld", "ART_src", DT, access="r")
rel("Access", "TP_bld", "ART_apk", DT, access="w")
rel("Realization", "SS_and", "C1", DT)

# ======================================================================
# FASES E-F — oportunidades, gaps e migração
# ======================================================================
EF = "E-F. Roadmap"
el("PL0", "Plateau", "Baseline (nov/2026)", "Três pilhas, servidor no celular velho, rede de casa.", EF)
el("PL1", "Plateau", "Transição 1: núcleo Python testado",
   "Domínio, calendário e SQLite com pytest; uma CLI mínima no PC já registra e mostra a folha.", EF)
el("PL2", "Plateau", "Transição 2: app Flet no PC", "Mesmas telas do celular rodando com `uv run`.", EF)
el("PL3", "Plateau", "Target: APK offline no celular", "App instalado, sem rede, com backup.", EF)
rels("Triggering", [("PL0", "PL1"), ("PL1", "PL2"), ("PL2", "PL3")], EF)
GAPS = [("GE1", "Eliminar servidor, API e API key", "eliminate", ["AB1", "TB_old", "TB_net"]),
        ("GE2", "Eliminar React, Flutter e regras em Dart", "eliminate", ["AB2", "AB3", "AB5"]),
        ("GE3", "Eliminar orquestrador, skills e Mongo/Docker", "eliminate", ["AB4", "TB_dock"]),
        ("GE4", "Manter regras de status e vocabulário", "keep", ["DO_ctr", "AC_dom"]),
        ("GE5", "Criar app Python offline com SQLite", "create", ["AC_app", "AC_repo", "TD"]),
        ("GE6", "Criar calendário de feriados e emendas", "create", ["AC_cal", "AC_lib", "DO_cal"]),
        ("GE7", "Criar fechamento do mês (pendências + folha)", "create", ["AS4", "AS5", "T3", "T4"]),
        ("GE8", "Criar backup e restauração", "create", ["AC_bkp", "DO_bkp"]),
        ("GB1", "Eliminar anotações no WhatsApp", "eliminate", ["B1", "B2", "BO_whats"]),
        ("GB2", "Trocar a pesquisa de feriados por sugestão do app", "eliminate + create", ["B3", "T2"])]
for key, name, op, targets in GAPS:
    el(key, "Gap", name, f"Operação: {op}.", EF, operacao=op)
    rels("Association", [(key, "PL0"), (key, "PL3")] + [(key, t) for t in targets], EF)
WPS = [("WP1", "WP1 Limpar o repositório", "Remover Django, React, Flutter, orquestrador, skills, Mongo/Docker. Escrever o ADR-002.", ["GE1", "GE2", "GE3"]),
       ("WP2", "WP2 Domínio + contrato em Python", "Status, validação, ordem, horas e extra; vetores golden em pytest.", ["GE4"]),
       ("WP3", "WP3 Repositório SQLite", "Schema, migrações e upsert por data.", ["GE5"]),
       ("WP4", "WP4 Calendário", "lib holidays BR/SP, regra de emenda, datas de Cubatão.", ["GE6", "GB2"]),
       ("WP5", "WP5 Telas Flet", "Hoje (bater ponto), Mês, Folha, Ajustes.", ["GE5", "GE7", "GB1"]),
       ("WP6", "WP6 Exportação e backup", "Folha em texto/CSV, backup/restauração JSON.", ["GE8"]),
       ("WP7", "WP7 APK e CI", "flet build apk, teste de não-rede, workflow único.", ["GE5"])]
FEITOS = {"WP1": "concluído em 2026-11-05", "WP2": "concluído em 2026-11-05", "WP3": "concluído em 2026-11-05", "WP4": "concluído em 2026-11-05", "WP5": "concluído em 2026-11-05", "WP6": "concluído em 2026-11-05",
          "WP7": "configurado em 2026-11-05; falta o 1º build no CI"}
for key, name, doc, gaps in WPS:
    el(key, "WorkPackage", name, doc, EF, status=FEITOS.get(key, "a fazer"))
    rels("Association", [(key, g) for g in gaps], EF)
rels("Triggering", [("WP1", "WP2"), ("WP2", "WP3"), ("WP2", "WP4"), ("WP3", "WP5"), ("WP4", "WP5"),
                    ("WP5", "WP6"), ("WP6", "WP7")], EF)
el("DL1", "Deliverable", "Repositório limpo + ADR-002", "README, CLAUDE.md e docs atualizados.", EF)
el("DL2", "Deliverable", "Pacote folha_ponto testado", "Domínio, calendário e SQLite com pytest verde.", EF)
el("DL3", "Deliverable", "App Flet funcional no PC", "Todos os casos de uso navegáveis.", EF)
el("DL4", "Deliverable", "APK offline + CI", "Instalável no celular.", EF)
rels("Realization", [("WP1", "DL1"), ("WP2", "DL2"), ("WP3", "DL2"), ("WP4", "DL2"), ("WP5", "DL3"),
                     ("WP6", "DL3"), ("WP7", "DL4"), ("DL1", "PL1"), ("DL2", "PL1"), ("DL3", "PL2"),
                     ("DL4", "PL3"), ("DL4", "ART_apk")], EF)


# ======================================================================
# VIEWS
# ======================================================================
class View:
    def __init__(self, name: str, doc: str, sub: str | None, viewpoint: str | None = None):
        parent = folder("diagrams", sub) if sub else TOP["diagrams"]
        a = {T: "archimate:ArchimateDiagramModel", "name": name, "id": nid()}
        if viewpoint:
            a["viewpoint"] = viewpoint
        self.v = ET.SubElement(parent, "element", a)
        ET.SubElement(self.v, "documentation").text = doc
        self.obj: dict[str, ET.Element] = {}
        self.parent_of: dict[str, str] = {}

    def node(self, key, x, y, w=170, h=60, parent=None, fill=None):
        a = {T: "archimate:DiagramObject", "id": nid(), "archimateElement": E[key]}
        if fill:
            a["fillColor"] = fill
        d = ET.SubElement(parent if parent is not None else self.v, "child", a)
        ET.SubElement(d, "bounds", {"x": str(x), "y": str(y), "width": str(w), "height": str(h)})
        self.obj[E[key]] = d
        return d

    def row(self, keys, y, x=20, w=170, h=60, gap=25, parent=None, fill=None):
        for i, k in enumerate(keys):
            if k:
                self.node(k, x + i * (w + gap), y, w, h, parent, fill(k) if callable(fill) else fill)

    def group(self, name, x, y, w, h, fill=None):
        a = {T: "archimate:Group", "id": nid(), "name": name}
        if fill:
            a["fillColor"] = fill
        g = ET.SubElement(self.v, "child", a)
        ET.SubElement(g, "bounds", {"x": str(x), "y": str(y), "width": str(w), "height": str(h)})
        return g

    def note(self, text, x, y, w, h, fill="#fffbe6"):
        n = ET.SubElement(self.v, "child", {T: "archimate:Note", "id": nid(), "textAlignment": "1",
                                            "fillColor": fill})
        ET.SubElement(n, "bounds", {"x": str(x), "y": str(y), "width": str(w), "height": str(h)})
        ET.SubElement(n, "content").text = text

    def finish(self, drop=lambda kind, s, t: False):
        """Desenha toda relação do modelo cujas duas pontas estão na view,
        exceto as que `drop(tipo_relação, chave_origem, chave_destino)` mandar omitir."""
        tc: dict[str, list[str]] = {}
        for rid, kind, s, t in RELS_ALL:
            if s not in self.obj or t not in self.obj or drop(kind, KEY[s], KEY[t]):
                continue
            so, to = self.obj[s], self.obj[t]
            c = ET.SubElement(so, "sourceConnection", {T: "archimate:Connection", "id": nid(),
                                                       "source": so.get("id"), "target": to.get("id"),
                                                       "archimateRelationship": rid})
            tc.setdefault(to.get("id"), []).append(c.get("id"))
        for d in self.v.iter("child"):
            if d.get("id") in tc:
                d.set("targetConnections", " ".join(tc[d.get("id")]))


KEY = {v: k for k, v in E.items()}
kind = lambda key: KIND[E[key]]
KEEP, ELIM, CREATE = "#c8e6c9", "#f7c6b5", "#fff3b0"
OP_COLOR = {"keep": KEEP, "eliminate": ELIM, "create": CREATE, "eliminate + create": "#f3d9a4"}

# ---- visão geral: o passo a passo do sistema (camadas) ----
COL = [190 + i * 215 for i in range(5)]           # colunas alinhadas entre as camadas
comp_comp = lambda k, s, t: k == "Serving" and kind(s) == kind(t) == "ApplicationComponent"
v = View("Passo a passo: bater o ponto e fechar o mês",
         "Visão em camadas (negócio → aplicação → tecnologia) dos dois fluxos que justificam o app.", None, "layered")
g = v.group("Negócio: o que o Trabalhador faz", 20, 20, 1300, 200, "#fff8d6")
v.node("EV_mark", COL[0], 30, 170, 50, g); v.node("EV_fim", COL[2], 30, 170, 50, g)
v.row(["T1", "T2", "T3", "T4", "B5"], 115, x=COL[0], w=170, gap=45, parent=g)
g = v.group("Aplicação: pacote Python folha_ponto", 20, 240, 1300, 330, "#e0f4fa")
v.row(["AS1", "AS3", "AS4", "AS5"], 35, x=COL[0], w=170, gap=45, parent=g)
v.node("AC_lib", COL[0], 140, 170, 60, g)
v.node("AC_cal", COL[1], 140, 170, 60, g); v.node("AC_dom", COL[2], 140, 170, 60, g)
v.node("AC_repo", COL[3], 140, 170, 60, g)
v.node("DO_cal", COL[1], 250, 170, 60, g); v.node("DO_reg", COL[2], 250, 170, 60, g)
v.node("DO_folha", COL[4], 250, 170, 60, g)
g = v.group("Tecnologia: tudo dentro do celular", 20, 590, 1300, 120, "#e3f2d9")
v.node("ART_db", COL[1] + 100, 35, 200, 60, g); v.node("SS_sql", COL[3], 35, 170, 60, g)
v.node("TD", COL[4], 35, 170, 60, g)
v.note("1. Chegou ao trabalho (evento): toca em \"Registrar Entrada\" (T1).\n"
       "2. Registrar marcação valida a ordem e grava a hora no Lançamento do dia; o status é recalculado.\n"
       "3. Durante o mês, o Calendário (lib holidays + datas de Cubatão) sugere feriados e emendas (T2).\n"
       "4. Fim do mês (evento): Listar pendências mostra dias úteis sem lançamento ou incompletos (T3).\n"
       "5. Gerar folha monta os dias 01–31 na ordem do papel: Manhã, Tarde, Extra (T4).\n"
       "6. O Trabalhador copia à mão e entrega a folha assinada.\n\nNada sai do celular: SQLite local, sem rede.",
       1340, 20, 340, 300)
v.finish(drop=lambda k, s, t: comp_comp(k, s, t) and (s, t) != ("AC_lib", "AC_cal"))

# ---- 0. Preliminar ----
v = View("Princípios de arquitetura", "Os cinco princípios que guiam a refatoração.", "0 - Preliminar", "motivation")
v.row(["G3", "G4", "G5"], 30, x=130, w=200, h=60, gap=200)
v.row(["P1", "P2", "P3", "P4", "P5"], 170, w=200, h=70, gap=30)
v.node("C1", 20, 320, 200, 60); v.node("C2", 480, 320, 200, 60)
v.finish()

# ---- A. Vision ----
SUB = "A - Vision"
v = View("Stakeholders, drivers e objetivos", "Por que refatorar: quem se importa, o que incomoda e o que se quer.",
         SUB, "stakeholder")
v.node("S_trab", 300, 20, 220, 60); v.node("S_emp", 880, 20, 220, 60)
v.row(["D1", "D3", "D2", "D4", "D5"], 140, w=190, gap=40)
v.row(["AS_1", None, "AS_2", "AS_3", "AS_4"], 270, w=190, gap=40)
v.row(["G1", "G2", "G3", "G4", "G5"], 400, w=190, gap=40)
v.finish()

v = View("Realização de objetivos", "Objetivos ← resultados ← requisitos e restrições (com o caso de uso).",
         SUB, "goal_realization")
v.row(["G1", None, "G2", "G3", "G4", "G5"], 20, w=175, gap=25)
v.row(["O1", "O2", "O3"], 140, x=20, w=175, gap=225)
v.row(["R4", "R5", "R3", "R2", "R1", None, "R6"], 270, w=160, gap=15)
v.node("C3", 20, 390, 160, 60); v.node("C1", 620, 140, 175, 60); v.node("C2", 1220, 140, 175, 60)
v.finish()

v = View("Capacidades e subdomínios (DDD)",
         "Capacidades que o curso de ação exige, com o subdomínio DDD (Core/Generic/Supporting) nas propriedades.", SUB)
v.node("COA", 330, 20, 300, 60)
v.row(["CAP1", "CAP3", "CAP2", "CAP4"], 140, w=210, gap=30)
v.row(["O3", "O1", "O2", "G5"], 260, w=210, gap=30)
v.row(["G3", "G4"], 20, x=700, w=150, gap=20)
v.note("Core: Registro de jornada, Fechamento da folha (in-house: é onde vai o esforço).\n"
       "Generic: lib holidays, SQLite, Flet (adotar pronto).\n"
       "Supporting: emendas, feriados de Cubatão, backup (sob medida, simples).", 20, 360, 940, 70)
v.finish()

# ---- B. Business ----
SUB = "B - Business"
v = View("1. Atores e papéis", "Quem participa: o Trabalhador anota e preenche; a Empresa recebe.", SUB, "organization")
v.row(["A_trab", "RO_dono"], 30, w=190, gap=100)
v.row(["A_emp", "RO_rec"], 130, w=190, gap=100)
v.finish()

no_assign = lambda k, s, t: k == "Assignment"
v = View("2. Baseline - processo atual (WhatsApp)",
         "Hoje: anotações soltas e garimpo no fim do mês. Todos os processos são do papel Responsável pelo ponto.", SUB)
v.row(["EV_mark", "B1", "BO_whats"], 30, w=180, gap=40)
v.row(["EV_fim", "B2", "B3", "B4", "B5"], 160, w=180, gap=40)
v.row([None, None, "BO_calm", "BO_folha", "RO_rec"], 290, w=180, gap=40)
v.note("A cada marcação, uma mensagem no WhatsApp. No fim do mês, tudo é reconstruído à mão.", 680, 30, 400, 60)
v.finish(drop=no_assign)

v = View("3. Target - processo futuro (app)",
         "Amanhã: um toque na hora; no fim do mês, a folha pronta para copiar. Todos os processos são do papel "
         "Responsável pelo ponto. Os requisitos atendidos estão na view A - Realização de objetivos.", SUB)
X = lambda c: 20 + c * 210
v.node("EV_mark", X(0), 20, 180, 55); v.node("EV_fim", X(2), 20, 180, 55)
v.row(["T1", "T2", "T3", "T4", "B5"], 140, w=180, gap=30)
v.node("BO_reg", X(1), 280, 180, 60); v.node("BO_folha", X(3), 280, 180, 60)
v.node("RO_rec", X(4), 280, 180, 60); v.node("T6", X(5), 280, 180, 60)
v.finish(drop=no_assign)


def gap_view(name, doc, sub, gaps):
    """Uma linha por gap: o que sai (baseline) à esquerda, o que fica/entra (target) à direita."""
    v = View(name, doc, sub)
    left_w, right_x = 3 * 175, 3 * 175 + 400
    v.group("Baseline: eliminar", 10, 10, left_w + 20, 60 + 80 * len(gaps), "#fbe9e4")
    v.group("Target: manter ou criar", right_x - 10, 10, 4 * 175 + 20, 60 + 80 * len(gaps), "#eef7e8")
    for i, (key, _, op, targets) in enumerate(gaps):
        y = 50 + i * 80
        v.node(key, left_w + 50, y, 320, 58, fill=OP_COLOR[op])
        shown = [t for t in targets if LAYER[KIND[E[t]]] in LAYERS_OF[sub]]
        out = [t for t in shown if op.startswith("eliminate") and t in BASELINE]
        inn = [t for t in shown if t not in out]
        for j, t in enumerate(reversed(out)):
            v.node(t, left_w - 160 - j * 175, y, 160, 58, fill=ELIM)
        for j, t in enumerate(inn):
            v.node(t, right_x + j * 175, y, 160, 58, fill=KEEP if op == "keep" else CREATE)
    v.note("Leia por linha: o gap no meio, o que sai à esquerda e o que fica ou entra à direita. "
           "As associações gap → elemento estão no modelo (Analysis ▸ Model Relations).",
           left_w + 50, 60 + 80 * len(gaps), 320, 75)
    v.finish(drop=lambda k, s, t: True)


BASELINE = {"AB1", "AB2", "AB3", "AB4", "AB5", "TB_old", "TB_net", "TB_dock", "B1", "B2", "B3", "BO_whats"}
LAYERS_OF = {"B - Business": {"business"}, "C - Information Systems": {"application", "technology"}}
gap_view("4. Gap analysis - negócio", "O que sai e o que entra no processo do Trabalhador.", SUB, GAPS[8:])

# ---- C. Information Systems ----
SUB = "C - Information Systems"
v = View("1. Baseline - aplicações atuais", "Três pilhas para o mesmo domínio, mais a infraestrutura de agentes.", SUB,
         "application_cooperation")
v.node("AB5", 260, 20, 220, 60)
v.row(["AB1", "AB2", "AB3", "AB4"], 150, w=200, gap=40)
v.row(["DB_srv", None, "DB_fl"], 280, w=200, gap=40)
v.finish()

v = View("2. Target - componentes do app",
         "Um pacote Python em módulos; a UI só fala com o domínio e o calendário, e só o repositório fala SQL.", SUB,
         "application_structure")
v.node("AC_app", 20, 20, 1060, 55)
v.node("AI_tel", 20, 150, 180, 60); v.node("AC_ui", 240, 150, 180, 60)
v.node("AC_dom", 460, 150, 180, 60); v.node("AC_bkp", 680, 150, 180, 60)
v.node("AC_cal", 460, 280, 180, 60); v.node("AC_repo", 680, 280, 180, 60)
v.node("AC_lib", 240, 280, 180, 60); v.node("DO_ctr", 900, 280, 180, 60)
v.note("A propriedade 'modulo' de cada componente é a pasta dele em folha_ponto/.", 900, 150, 180, 70)
v.finish()

v = View("3. Target - serviços x casos de uso",
         "Cada serviço de aplicação atende casos de uso (propriedade) e serve um processo do target.", SUB)
STEP = 170
cx = lambda c: 20 + int(c * STEP)
v.row(["AS1", "AS2", "AS4", "AS5", "AS3", "AS7", "AS6"], 170, w=150, gap=STEP - 150)
for key, c in [("T1", 0), ("T3", 1.5), ("T4", 3), ("T2", 4.5), ("T6", 6)]:
    v.node(key, cx(c), 20, 150, 60)
for key, c in [("AC_dom", 1.5), ("AC_cal", 4), ("AC_repo", 5), ("AC_bkp", 6)]:
    v.node(key, cx(c), 320, 150, 60)
v.finish(drop=lambda k, s, t: comp_comp(k, s, t) or k in ("Flow", "Triggering"))

v = View("4. Dados", "Objetos de dados, quem lê (r) e quem escreve (w).", SUB)
v.row(["AS1", "AS2", "AS4", "AS5", "AS3", "AS7", "AS6"], 20, w=150, gap=20)
v.row(["DO_reg", "DO_folha", "DO_cal", "DO_pref", "DO_bkp"], 200, x=100, w=180, gap=45)
v.row(["BO_reg", "BO_folha"], 360, x=100, w=180, gap=45)
v.row(["AC_dom", "DO_ctr"], 360, x=700, w=180, gap=45)
v.finish()

gap_view("5. Gap analysis - aplicações e tecnologia",
         "Verde = manter, vermelho = eliminar, amarelo = criar. Baseline à esquerda, target à direita.", SUB, GAPS[:8])

# ---- D. Technology ----
SUB = "D - Technology"
v = View("1. Baseline - tecnologia atual", "O app só funciona na Wi-Fi de casa, servido por um celular velho.", SUB)
v.node("TB_net", 260, 20, 220, 60)
v.row(["TB_old", "TB_pc", "TB_dock", "TB_ci"], 150, w=200, gap=40)
v.row(["AB1", "AB2", "AB4"], 280, x=20, w=200, gap=40)
v.finish()

v = View("2. Target - tecnologia (celular e PC)",
         "Em uso: só o celular, sem rede. No desenvolvimento: o PC com uv testa e gera o APK.", SUB)
g = v.group("Celular Android (uso, 100% offline)", 20, 20, 700, 430, "#e3f2d9")
v.node("TD", 250, 30, 200, 60, g)
v.row(["SS_py", "SS_sql", "SS_and"], 130, x=20, w=200, gap=30, parent=g)
v.row(["ART_apk", "ART_db", "TS_sto"], 240, x=20, w=200, gap=30, parent=g)
v.row(["ART_bkp", "TS_sha"], 345, x=20, w=200, gap=30, parent=g)
g = v.group("PC (desenvolvimento)", 760, 20, 480, 430, "#eeeeee")
v.node("ND_pc", 20, 30, 200, 60, g); v.node("SS_test", 250, 30, 200, 60, g)
v.node("SS_uv", 250, 130, 200, 60, g); v.node("ART_src", 20, 240, 200, 60, g)
v.node("TP_bld", 250, 240, 200, 60, g); v.node("SS_ci", 250, 345, 200, 60, g)
v.row(["AC_app", "AC_bkp", "AC_repo"], 490, x=40, w=200, gap=30)
v.finish(drop=lambda k, s, t: kind(s) == "ApplicationComponent" or s == "SS_test")

# ---- E-F ----
SUB = "E-F - Oportunidades e Migração"
v = View("1. Roadmap: platôs, entregas e pacotes de trabalho",
         "Baseline → Transição 1 → Transição 2 → Target, em incrementos que já funcionam (arquiteturas de transição).", SUB)
C = lambda c: 20 + int(c * 210)
for key, c in [("PL0", 0), ("PL1", 1.5), ("PL2", 3.5), ("PL3", 5)]:
    v.node(key, C(c), 20, 190, 60, fill="#f5e0e6")
for key, c in [("DL1", 0.5), ("DL2", 1.5), ("DL3", 3.5), ("DL4", 5)]:
    v.node(key, C(c), 150, 190, 60)
for key, c, y in [("WP1", 0, 290), ("WP2", 1, 290), ("WP3", 2, 290), ("WP4", 2, 390), ("WP5", 3, 290),
                  ("WP6", 4, 290), ("WP7", 5, 290)]:
    v.node(key, C(c), y, 190, 60)
v.finish()

v = View("2. Gaps x pacotes de trabalho", "Cada gap consolidado (fase E) é resolvido por um ou mais pacotes.", SUB)
gy = {}
for i, (key, _, op, _) in enumerate(GAPS):
    gy[key] = 20 + i * 70
    v.node(key, 20, gy[key], 380, 52, fill=OP_COLOR[op])
for i, (key, *_r) in enumerate(WPS):
    v.node(key, 620, 20 + i * 100, 260, 52)
v.finish(drop=lambda k, s, t: k == "Triggering")

# ----------------------------------------------------------------- saída
purpose = ET.SubElement(root, "purpose")
purpose.text = ("Arquitetura da Folha de Ponto Pessoal v2: app 100% offline no celular, em Python com uv. "
                "Método: TOGAF ADM (Preliminar, A, B, C, D, E-F) com baseline, target e gap analysis. "
                "Casos de uso em docs/casos-de-uso.md. Gerado por docs/arquitetura/gera_modelo.py — "
                "edite o script e gere de novo em vez de editar à mão.")
ET.indent(root)
DST.parent.mkdir(parents=True, exist_ok=True)
ET.ElementTree(root).write(DST, encoding="UTF-8", xml_declaration=True)
n_views = sum(1 for e in root.iter("element") if e.get(T) == "archimate:ArchimateDiagramModel")
print(f"ok: {len(KIND)} elementos, {len(RELS_ALL)} relações, {n_views} views -> {DST}")
