# Diretrizes para Claude Code (`CLAUDE.md`)

Este arquivo contém as instruções e convenções do projeto **Folha de Ponto Pessoal** para o **Claude Code (`claude`)**.

---

## 1. Papel no Ecossistema Multi-CLI

Quando acionado pelo orquestrador autônomo (`./orchestrator.sh`), seu papel é o de **Builder**:
1. Leia a tarefa em `.agent_bus/current_task.md`.
2. Verifique os bloqueios ou feedbacks em `.agent_bus/feedback.md`.
3. Implemente o código necessário seguindo a arquitetura do projeto.
4. Crie/atualize testes automatizados cobrindo suas alterações.
5. Verifique se os testes locais passam antes de concluir.
6. Ao finalizar a rodada, escreva um resumo objetivo em `.agent_bus/builder_output.md`.

---

## 2. Estrutura do Projeto e Stacks

- **Backend** (`src/backend`):
  - Framework: Django 5 + Django REST Framework.
  - Banco de dados: SQLite local (`db.sqlite3`).
  - Gerenciador de dependências: `uv`.
  - Arquitetura em camadas estrita:
    - `views.py` (APIView, autenticação via `X-Api-Key`, delegação).
    - `serializers.py` (Validação baseada em `domain_generated.py`).
    - `services.py` (`TimeRecordService` - regras de cálculo e negócio).
    - `repositories.py` (`TimeRecordRepository` - queries ORM SQLite).
    - `models.py` (`TimeRecord`).

- **Frontend Web** (`src/web`):
  - Stack: React 19 + TypeScript + Vite.
  - Gerenciador: `npm`.
  - Componentes principais em `src/web/src/components/` (`TodayTab`, `MonthTab`, `RecordForm`, `RecordCard`, `ApiKeyGate`).

- **Contratos Compartilhados** (`contracts/`):
  - Fonte única da verdade: `contracts/time_record.json`.
  - Gerador de código: `python3 contracts/generate.py`.
  - Nunca edite `domain_generated.py`, `domain.generated.ts` ou `domain.g.dart` manualmente.

- **Mobile** (`src/mobile`):
  - Flutter app Android.

---

## 3. Comandos Essenciais de Desenvolvimento

```bash
# Validação de contratos
python3 contracts/generate.py --check
python3 contracts/generate.py          # Se atualizar o JSON de contrato

# Testes do Backend
cd src/backend && uv run python manage.py test

# Build e Typecheck do Frontend
cd src/web && npm run build

# Servidor de Desenvolvimento Backend
cd src/backend && uv run python manage.py runserver 0.0.0.0:8000

# Servidor de Desenvolvimento Frontend
cd src/web && npm run dev
```

---

## 4. Regras Obrigatórias

- **100% Offline / Local-First**: Não adicione chamadas HTTP para serviços externos ou CDNs.
- **Autenticação**: Todos os endpoints de dados requerem cabeçalho `X-Api-Key`.
- **Testes Obrigatórios**: Qualquer nova funcionalidade ou correção de bug deve vir acompanhada de testes unitários ou de integração.
- **Respeito às Camadas**: Nunca faça queries de banco diretamente em `views.py` ou `serializers.py`; use o `TimeRecordRepository` através do `TimeRecordService`.
