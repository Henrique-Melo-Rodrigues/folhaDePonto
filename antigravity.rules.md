# Regras de Auditoria e Revisão do Antigravity (`antigravity.rules.md`)

Este arquivo define as diretrizes rigorosas que o **Antigravity (`agy`)** deve seguir ao auditar o código produzido pelo Builder no ciclo autônomo.

---

## 1. Critérios de Avaliação (5 Eixos + Regra de Ouro)

### 🌟 Regra de Ouro: Local-First & 100% Offline
- **Zero Vazamento de Rede**: Rejeite (`REVISE`) qualquer código que adicione requisições para domínios externos, CDNs, telemetria remota ou URLs não locais.
- **Persistência Local**: Dados devem permanecer no SQLite embarcado ou storage local do cliente.
- **Assets Locais**: Fontes, ícones e scripts devem ser empacotados na compilação.

### 1. Correção (Correctness)
- O código atende exatamente ao solicitado em `.agent_bus/current_task.md`?
- Casos de borda (valores nulos, strings vazias, horários invertidos, timezone) foram tratados?
- Foram adicionados testes automatizados que cobrem os novos caminhos de execução?

### 2. Contratos de Domínio (`contracts/`)
- A fonte da verdade para vocabulário de domínio (`DAY_TYPES`, `STATUSES`, `TIME_FIELDS`) é `contracts/time_record.json`.
- Nenhum arquivo gerado (`domain_generated.py`, `domain.generated.ts`, `domain.g.dart`) deve ser editado manualmente sem sincronizar o gerador `contracts/generate.py`.

### 3. Arquitetura e Padrões
- **Backend (Django)**: Respeitar a separação estrita em camadas:
  - `views.py`: Apenas recepção HTTP, autenticação e delegação.
  - `serializers.py`: Validação e normalização de dados.
  - `services.py`: Regras de negócio e cálculo de status.
  - `repositories.py`: Acesso ao banco de dados via ORM.
  - `models.py`: Definição de tabelas.
- **Frontend (React/TS)**: Tipagem estrita com TypeScript, componentes limpos e isolamento de estado.

### 4. Segurança
- Todos os endpoints protegidos exigem o cabeçalho `X-Api-Key`.
- Nenhuma chave de API, segredo ou senha hardcoded no código fonte.
- Sanitização de inputs contra injeção e XSS.

### 5. Performance e Limpeza
- Ausência de loops infinitos, consultas N+1 no ORM ou renderizações desnecessárias.
- Ausência de arquivos temporários, logs de debug ou prints esquecidos no código.

---

## 2. Formato Obrigatório do Relatório de Feedback

O Antigravity **DEVE** estruturar seu feedback no arquivo `.agent_bus/feedback.md` seguindo exatamente o formato abaixo:

```markdown
## Verdict
APPROVED ou REVISE

## Summary
[Resumo conciso de 1-3 frases sobre as alterações auditadas]

## Blocker Issues
- [caminho/do/arquivo:linha] Descrição precisa do problema e como corrigi-lo. (Obrigatório se REVISE)

## Non-Blocker Suggestions
- [caminho/do/arquivo:linha] Sugestão de melhoria ou refatoração opcional.

## Verification Checklist
- [x] Conformidade 100% Offline / Local-first
- [x] Contratos sincronizados (contracts/generate.py)
- [x] Testes unitários/integração adequados
- [x] Separação em camadas mantida
- [x] Segurança e autenticação validadas
```

---

## 3. Regras de Decisão do Veredito

- **`APPROVED`**: Concedido APENAS quando não houver NENHUM `Blocker Issue` e todos os critérios de conformidade forem atendidos.
- **`REVISE`**: Obrigatório se houver qualquer falha de teste, quebra de contrato, violação de arquitetura, falha de segurança ou dependência de rede externa.
