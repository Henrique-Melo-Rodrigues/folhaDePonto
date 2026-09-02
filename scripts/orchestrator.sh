#!/usr/bin/env bash
# ==============================================================================
# ORQUESTRADOR MULTI-CLI: Claude Code (Builder) + Antigravity (Auditor)
# ==============================================================================
set -eo pipefail

TASK_DESCRIPTION="${1:-}"

if [ -z "$TASK_DESCRIPTION" ]; then
  echo "=================================================================="
  echo "  ERRO: Forneça a descrição da tarefa para iniciar o ciclo."
  echo "=================================================================="
  echo "Uso: ./orchestrator.sh \"<descrição da tarefa>\""
  echo "Exemplo: ./orchestrator.sh \"Validar que hora de saída seja posterior à entrada\""
  exit 1
fi

# Detecta ferramentas necessárias
CLAUDE_BIN="$(which claude 2>/dev/null || true)"
AGY_BIN="$(which agy 2>/dev/null || which antigravity 2>/dev/null || true)"

if [ -z "$CLAUDE_BIN" ]; then
  echo "✖ Erro: Claude Code CLI ('claude') não foi encontrado no PATH."
  exit 1
fi

if [ -z "$AGY_BIN" ]; then
  echo "✖ Erro: Antigravity CLI ('agy') não foi encontrado no PATH."
  exit 1
fi

# Diretório raiz do projeto
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

BASE_BRANCH="$(git branch --show-current 2>/dev/null || echo "main")"
if [ -z "$BASE_BRANCH" ]; then
  BASE_BRANCH="main"
fi

MAX_ROUNDS="${MAX_ROUNDS:-5}"
ROUND=1
BRANCH_NAME="agent/task-$(date +%s)"

echo "=================================================================="
echo "  INICIANDO ORQUESTRAÇÃO MULTI-CLI"
echo "  Base Branch: $BASE_BRANCH | Staging Branch: $BRANCH_NAME"
echo "  Max Rodadas: $MAX_ROUNDS"
echo "  Tarefa: $TASK_DESCRIPTION"
echo "=================================================================="

# Inicializa Barramento (.agent_bus)
mkdir -p .agent_bus
echo "$TASK_DESCRIPTION" > .agent_bus/current_task.md
cat << 'EOF_FEEDBACK' > .agent_bus/feedback.md
## Verdict
REVISE

## Blocker Issues
- Execução inicial necessária com base no arquivo .agent_bus/current_task.md
EOF_FEEDBACK

# Prepara branch de staging
git checkout -b "$BRANCH_NAME"

while [ "$ROUND" -le "$MAX_ROUNDS" ]; do
  echo ""
  echo "=========================================================="
  echo "  CICLO AUTÔNOMO: RODADA $ROUND DE $MAX_ROUNDS"
  echo "=========================================================="

  # ----------------------------------------------------
  # ETAPA 1: BUILDER (Claude Code)
  # ----------------------------------------------------
  echo "▶ [1/4] Claude Code executando implementação (Builder)..."
  claude --dangerously-skip-permissions -p \
    "Você é o Builder. Leia .agent_bus/current_task.md e .agent_bus/feedback.md. Siga as instruções em CLAUDE.md. Implemente o código e os testes necessários. Ao finalizar, gere .agent_bus/builder_output.md." || true

  # Registra progresso no git local se houver alterações
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "chore(agent): alterações Claude Code (Rodada $ROUND)" || true
  fi

  # ----------------------------------------------------
  # ETAPA 2: TRIAGEM DETERMINÍSTICA LOCAL (Zero Tokens LLM)
  # ----------------------------------------------------
  echo "▶ [2/4] Executando gatekeeper de testes locais..."
  FAIL_GATEKEEPER=0
  GATEKEEPER_LOG=""

  # 2.1 Verificação de integridade de contratos
  if [ -f "contracts/generate.py" ]; then
    if ! CONTRACT_CHECK_OUTPUT=$(python3 contracts/generate.py --check 2>&1); then
      FAIL_GATEKEEPER=1
      GATEKEEPER_LOG="[Contratos Fora de Sincronia]\n$CONTRACT_CHECK_OUTPUT\n"
    fi
  fi

  # 2.2 Testes do backend Django (se contratos estiverem ok)
  if [ "$FAIL_GATEKEEPER" -eq 0 ] && [ -d "src/backend" ]; then
    if ! BACKEND_TEST_OUTPUT=$(cd src/backend && uv run python manage.py test 2>&1); then
      FAIL_GATEKEEPER=1
      GATEKEEPER_LOG="${GATEKEEPER_LOG}[Falha nos Testes Django]\n$BACKEND_TEST_OUTPUT\n"
    fi
  fi

  # 2.3 Build / Typecheck do frontend React
  if [ "$FAIL_GATEKEEPER" -eq 0 ] && [ -d "src/web" ]; then
    if ! WEB_BUILD_OUTPUT=$(cd src/web && npm run build 2>&1); then
      FAIL_GATEKEEPER=1
      GATEKEEPER_LOG="${GATEKEEPER_LOG}[Falha no Build/Typecheck Web]\n$WEB_BUILD_OUTPUT\n"
    fi
  fi

  # 2.4 Testes Flutter (se flutter estiver instalado)
  if [ "$FAIL_GATEKEEPER" -eq 0 ] && [ -d "src/mobile/test" ] && which flutter >/dev/null 2>&1; then
    if ! MOBILE_TEST_OUTPUT=$(cd src/mobile && flutter test 2>&1); then
      FAIL_GATEKEEPER=1
      GATEKEEPER_LOG="${GATEKEEPER_LOG}[Falha nos Testes Flutter]\n$MOBILE_TEST_OUTPUT\n"
    fi
  fi

  # Interceptação de falha do Gatekeeper
  if [ "$FAIL_GATEKEEPER" -ne 0 ]; then
    echo "✖ Gatekeeper falhou. Redirecionando logs para o Claude Code..."
    cat << EOF_GATEKEEPER_FAIL > .agent_bus/feedback.md
## Verdict
REVISE

## Blocker Issues
- Falha na validação determinística local:
\`\`\`
$(echo -e "$GATEKEEPER_LOG" | tail -n 35)
\`\`\`
EOF_GATEKEEPER_FAIL
    ROUND=$((ROUND + 1))
    continue
  fi

  echo "✔ Gatekeeper passou com sucesso. Iniciando auditoria..."

  # ----------------------------------------------------
  # ETAPA 3: REVIEWER (Antigravity `agy`)
  # ----------------------------------------------------
  echo "▶ [3/4] Antigravity auditando alterações contra $BASE_BRANCH..."
  "$AGY_BIN" -p \
    "Você é o Auditor Sênior do projeto. Inspecione o git diff contra a branch $BASE_BRANCH seguindo as regras em antigravity.rules.md e GEMINI.md. Analise correção, arquitetura, segurança e conformidade 100% offline. Escreva o relatório rigoroso com veredito em .agent_bus/feedback.md." \
    --dangerously-skip-permissions || true

  # ----------------------------------------------------
  # ETAPA 4: AVALIAÇÃO DE CONVERGÊNCIA
  # ----------------------------------------------------
  echo "▶ [4/4] Avaliando veredito do barramento..."
  if [ -f ".agent_bus/feedback.md" ] && grep -q -i "## Verdict[[:space:]]*APPROVED" .agent_bus/feedback.md; then
    echo ""
    echo "=========================================================="
    echo "  ✔ CÓDIGO APROVADO PELO ANTIGRAVITY NA RODADA $ROUND!"
    echo "=========================================================="
    git checkout "$BASE_BRANCH"
    git merge --ff-only "$BRANCH_NAME"
    echo "🚀 Branch '$BASE_BRANCH' atualizada via fast-forward com sucesso."
    rm -rf .agent_bus
    exit 0
  fi

  echo "⚠ Antigravity solicitou correções ou veredito não aprovado. Iniciando próxima rodada..."
  ROUND=$((ROUND + 1))
done

echo ""
echo "=========================================================="
echo "  ❌ LIMITE DE $MAX_ROUNDS RODADAS ATINGIDO SEM APROVAÇÃO"
echo "=========================================================="
echo "Inspecione .agent_bus/feedback.md e a branch '$BRANCH_NAME' para resolução manual."
exit 1
