#!/usr/bin/env bash
# Deploy completo para o celular (Termux): código via git push, frontend via
# rsync (o dist não é versionado), dependências, migrations e restart.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Build do frontend"
(cd src/web && npm run build)

echo "==> Enviando código (git push celular main)"
git push celular main

echo "==> Enviando build do frontend"
rsync -a src/web/dist celular:~/folhaDePonto/src/web/

echo "==> Dependências + migrations no celular"
ssh celular 'cd ~/folhaDePonto/src/backend && pip install -q -r requirements.txt && python manage.py migrate --no-input'

echo "==> Reiniciando servidor"
timeout 15 ssh celular './folha-restart.sh' < /dev/null || true

sleep 2
echo "==> Verificando"
curl -s -m 15 http://192.168.0.106:8000/api/health/ && echo " <- ok"
