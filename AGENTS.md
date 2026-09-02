# Catálogo de Agentes e Orquestração (`AGENTS.md`)

Este repositório possui uma infraestrutura de múltiplos agentes de IA preparados para trabalhar em conjunto ou individualmente no projeto **Folha de Ponto Pessoal**.

---

## 1. Visão Geral das CLIs

| CLI | Binário | Função Principal no Projeto | Configuração / Regras |
|---|---|---|---|
| **Claude Code** | `claude` | **Builder**: Implementa código, contratos, schemas e testes. | [CLAUDE.md](CLAUDE.md), `.claude/` |
| **Google Antigravity** | `agy` | **Reviewer / Auditor**: Audita arquitetura, segurança e regras offline. | [GEMINI.md](GEMINI.md), [antigravity.rules.md](antigravity.rules.md) |

---

## 2. Orquestração Autônoma (`orchestrator.sh`)

O script [`orchestrator.sh`](orchestrator.sh) orquestra um loop contínuo entre Claude Code e Antigravity:
1. **Builder (Claude Code)**: Consome `.agent_bus/current_task.md` e `.agent_bus/feedback.md`.
2. **Gatekeeper Local**: Executa `contracts/generate.py --check`, testes Django e build do React.
3. **Reviewer (Antigravity)**: Audita `git diff` e emite veredito em `.agent_bus/feedback.md`.
4. **Convergência**: Faz merge automático para a branch principal quando o veredito for `APPROVED`.

Documentação completa do fluxo: [gemini-code.md](gemini-code.md)

---

## 3. Personas Especializadas (`agents/`)

| Persona | Arquivo | Foco |
|---|---|---|
| `code-reviewer` | [agents/code-reviwer.md](agents/code-reviwer.md) | Revisão sênior em 5 eixos (Correção, Legibilidade, Arquitetura, Segurança, Performance). |
| `security-auditor` | [agents/security-auditor.md](agents/security-auditor.md) | Auditoria de segurança, OWASP, segredos e autenticação por API Key. |
| `test-engineer` | [agents/test-engineer.md](agents/test-engineer.md) | Estratégia de testes, análise de cobertura e padrão Prove-It. |

---

## 4. Comandos Rápidos e Skills

- **Comandos Slash** em `.claude/commands/`: `/plan`, `/build`, `/test`, `/review`, `/ship`, `/spec`, `/code-simplify`.
- **Skills Modulares** em `skills/`: 23 habilidades operacionais abrangendo TDD, refatoração, CI/CD, debugging e documentação.
