# Orquestração Multi-CLI: Antigravity & Claude Code (`gemini-code.md`)

Este documento define a arquitetura, o protocolo de comunicação e o fluxo operacional para a colaboração autônoma entre múltiplas CLIs de Inteligência Artificial — **Claude Code (`claude`)** e **Google Antigravity (`agy`)** — no projeto **Folha de Ponto Pessoal**.

---

## 1. Visão Geral da Arquitetura

O sistema opera no modelo **Builder-Auditor Loop** com **Gatekeeper Determinístico Local**:

```
+-----------------------------------------------------------------------+
|                           INÍCIO DA TAREFA                            |
|                 ./orchestrator.sh "<descrição da tarefa>"            |
+-----------------------------------------------------------------------+
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │   Prepara Branch Staging    │
                     │  agent/task-<timestamp>     │
                     └──────────────┬──────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
        ▼                                                       │
┌──────────────────────────────┐                                │
│   FASE 1: BUILDER            │                                │
│   (Claude Code - `claude`)   │                                │
│   - Lê `.agent_bus/`         │                                │
│   - Implementa código/testes │                                │
│   - Gera `builder_output.md` │                                │
└──────────────┬───────────────┘                                │
               │                                                │
               ▼                                                │
┌──────────────────────────────┐                                │
│   FASE 2: GATEKEEPER LOCAL   │                                │
│   (Zero Consumo de LLM)      │                                │
│   - `contracts/generate.py`  │                                │
│   - `uv run manage.py test`  │  ✖ Falha (Testes Quebrados)    │
│   - `npm run build`          ├────────────────────────────────┤
└──────────────┬───────────────┘                                │
               │ ✔ Sucesso                                      │
               ▼                                                │
┌──────────────────────────────┐                                │
│   FASE 3: REVIEWER / AUDITOR │                                │
│   (Antigravity - `agy`)      │                                │
│   - Inspeciona `git diff`    │                                │
│   - Aplica `antigravity.rules`│                                │
│   - Gera parecer estruturado │                                │
└──────────────┬───────────────┘                                │
               │                                                │
               ▼                                                │
┌──────────────────────────────┐                                │
│   FASE 4: CONVERGÊNCIA       │                                │
│   Avaliação do `.agent_bus`  │                                │
└──────┬────────────────┬──────┘                                │
       │                │                                       │
       │ REVISE         │ APPROVED                              │
       │                │                                       │
       │                ▼                                       │
       │     ┌─────────────────────────────┐                    │
       │     │ Fast-Forward Merge em main  │                    │
       │     │ 🚀 TAREFA CONCLUÍDA         │                    │
       │     └─────────────────────────────┘                    │
       │                                                        │
       └────────────────────────────────────────────────────────┘
                       (Próxima Rodada: até 5)
```

---

## 2. Divisão de Atribuições

| Papel | CLI Responsável | Foco Principal | Responsabilidades |
|---|---|---|---|
| **Builder** (Construtor) | **Claude Code** (`claude`) | Implementação & Refatoração | - Implementar funcionalidades no backend (Django/uv) e frontend (React/Vite).<br>- Criar e atualizar testes unitários e de integração.<br>- Manter a integridade de contratos em `contracts/time_record.json`.<br>- Resolver bloqueios apontados no `.agent_bus/feedback.md`. |
| **Gatekeeper** (Triagem) | **Engine Local** (Bash/OS) | Validação Determinística | - Zero consumo de tokens de IA.<br>- Validação de contratos (`contracts/generate.py --check`).<br>- Execução da suíte Django (20+ testes).<br>- Typechecking e build do Vite/TypeScript.<br>- Interceptação rápida de regressões. |
| **Reviewer / Auditor** | **Antigravity** (`agy`) | Qualidade, Segurança & Arquitetura | - Análise em 5 eixos: Correção, Legibilidade, Arquitetura, Segurança e Performance.<br>- Garantia de **Zero Network Leakage** (Operação 100% Offline / Local-First).<br>- Auditoria do `git diff` contra a branch base.<br>- Emissão de veredito estrito (`APPROVED` ou `REVISE`). |

---

## 3. Protocolo de Comunicação: `.agent_bus/`

A comunicação assíncrona e desacoplada entre as CLIs ocorre por arquivos Markdown temporários no diretório `.agent_bus/` (ignorado pelo git):

### 3.1. Arquivos do Barramento

1. **`.agent_bus/current_task.md`**
   - Criado no início do ciclo com a descrição da tarefa fornecida pelo usuário.
   - Imutável durante as rodadas para manter o alinhamento de escopo.

2. **`.agent_bus/feedback.md`**
   - Canal de comunicação do Gatekeeper e do Reviewer (Antigravity) para o Builder (Claude Code).
   - Estrutura obrigatória:
     ```markdown
     ## Verdict
     APPROVED | REVISE

     ## Blocker Issues
     - [arquivo:linha] Descrição objetiva do problema e ação necessária

     ## Non-Blocker Suggestions
     - [arquivo:linha] Melhorias opcionais

     ## Verification Story
     - Contratos validados: Sim/Não
     - Testes de backend: Sim/Não
     - Build de frontend: Sim/Não
     ```

3. **`.agent_bus/builder_output.md`**
   - Gerado pelo Claude Code ao final de cada rodada de implementação.
   - Resume as alterações feitas, arquivos tocados e testes adicionados/executados.

---

## 4. Regras Fundamentais do Projeto

### 4.1. Operação 100% Offline / Local-First
1. **Zero dependência de rede externa**: Nenhuma requisição HTTP para domínios públicos ou CDNs.
2. **Persistência local**: Banco de dados SQLite embarcado (`src/backend/db.sqlite3`).
3. **Assets bundled**: Fontes, ícones e scripts empacotados localmente no build do Vite.

### 4.2. Fonte Única da Verdade (`contracts/`)
- Todos os tipos de dias (`DAY_TYPES`), campos de horário (`TIME_FIELDS`), status (`STATUSES`) e padrões de validação são definidos em `contracts/time_record.json`.
- Nunca edite `domain_generated.py`, `domain.generated.ts` ou `domain.g.dart` manualmente. Execute sempre:
  ```bash
  python3 contracts/generate.py
  ```

### 4.3. Arquitetura em Camadas do Backend
```
views.py (APIView + Header X-Api-Key)
   ↓
serializers.py (Validação via domain_generated.py)
   ↓
services.py (TimeRecordService - regras de negócio e cálculo de status)
   ↓
repositories.py (TimeRecordRepository - ORM Django / SQLite)
   ↓
models.py (TimeRecord)
```

---

## 5. Como Executar a Orquestração

### 5.1. Execução Básica
Para disparar uma tarefa autônoma completa:

```bash
./orchestrator.sh "Adicionar validação para impedir hora de saída anterior à entrada"
```

### 5.2. Opções e Variáveis de Ambiente
- `MAX_ROUNDS`: Número máximo de rodadas de feedback (padrão: `5`).
  ```bash
  MAX_ROUNDS=8 ./orchestrator.sh "Refatorar componente MonthTab"
  ```
- `BASE_BRANCH`: Branch base de comparação (padrão: branch atual ou `main`).

---

## 6. Fluxo de Recuperação e Intervenção Manual

Se o limite de rodadas for atingido sem convergência:
1. O orquestrador preserva a branch `agent/task-<timestamp>`.
2. O desenvolvedor inspeciona `.agent_bus/feedback.md` e `.agent_bus/builder_output.md`.
3. Ajustes podem ser feitos manualmente ou reexecutando o orquestrador na mesma branch.
