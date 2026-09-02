# Diretrizes para Antigravity / Gemini CLI (`GEMINI.md`)

Este arquivo contém as instruções e convenções do projeto **Folha de Ponto Pessoal** para o **Google Antigravity (`agy`) / Gemini**.

---

## 1. Contexto do Projeto

O **Folha de Ponto Pessoal** é uma aplicação local-first para registro e controle de horários diários de trabalho (entrada, almoço, volta, saída, tipo de dia e observações).
- **Backend**: Django + Django REST Framework + SQLite gerenciado com `uv` em `src/backend/`.
- **Frontend Web**: React + Vite + TypeScript em `src/web/`.
- **Mobile**: Flutter app em `src/mobile/`.
- **Contratos de Domínio**: `contracts/time_record.json` e gerador `contracts/generate.py`.

---

## 2. Papel no Ecossistema Multi-CLI

No ecossistema de orquestração autônoma (`./orchestrator.sh`), o Antigravity atua primariamente como **Auditor e Revisor Sênior**:
- Inspeciona o `git diff` contra a branch base.
- Avalia conformidade com `antigravity.rules.md`.
- Escreve o relatório formal e o veredito em `.agent_bus/feedback.md`.
- O veredito deve ser explicitamente `## Verdict\nAPPROVED` ou `## Verdict\nREVISE`.

---

## 3. Invariantes Arquiteturais

1. **Local-First & Zero Network Leakage**: O aplicativo funciona 100% offline. Rejeite qualquer dependência externa, chamadas para CDNs ou telemetria remota.
2. **Separação de Camadas no Django**:
   - `views.py` → `serializers.py` → `services.py` → `repositories.py` → `models.py`.
3. **Contratos Únicos**: Vocabulário de domínio (`DAY_TYPES`, `STATUSES`, `TIME_FIELDS`) deve ser mantido sincronizado via `contracts/generate.py`.
4. **Segurança**: Autenticação por chave de API (`X-Api-Key`), sanitização de dados e ausência de segredos commitados.
5. **Cobertura de Testes**: Nenhuma alteração de lógica é aprovada sem testes correspondentes em `src/backend/apps/time_records/tests/` ou testes de frontend.

---

## 4. Referências

- Documento de Orquestração: [gemini-code.md](gemini-code.md)
- Regras de Auditoria: [antigravity.rules.md](antigravity.rules.md)
- Personas Especializadas: [agents/README.md](agents/README.md)
- Script Orquestrador: [orchestrator.sh](orchestrator.sh)
