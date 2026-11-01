#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "ERRO: criei .env de exemplo. Edite GEMINI_API_KEY e GEMINI_MODEL antes de iniciar."
  exit 1
fi
mkdir -p storage reports screenshots
if [[ -f erp.sqlite3 && ! -e storage/erp.sqlite3 ]]; then
  cp erp.sqlite3 storage/erp.sqlite3
  echo "Banco SQLite anterior copiado para storage/erp.sqlite3."
fi
docker compose config --quiet
docker compose build --pull --no-cache
docker compose up -d --force-recreate --remove-orphans
docker compose ps
echo
echo "ERP: http://127.0.0.1:5000"
echo "Chat: http://127.0.0.1:5000/controle"
echo "CLI: docker compose exec -it erp python -m rpa.cli"
echo "Testes: docker compose exec -T erp python -m pytest -q"
