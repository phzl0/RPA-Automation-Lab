#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "=== Containers ==="
docker compose ps
echo "=== Python e arquivos no container ==="
docker compose exec -T erp python -c "import sys, rpa.cli, erp.app; print(sys.version); print('CLI:', rpa.cli.__file__); print('ERP:', erp.app.__file__)"
echo "=== Saudação sem rede/sem API ==="
docker compose exec -T erp python -c "from rpa.interpreter import interpret; result=interpret('bom dia'); print(result); assert result['kind']=='chat' and result.get('action') is None"
echo "=== Coluna CEP e banco utilizado ==="
docker compose exec -T erp python -c "import os, sqlite3; p=os.environ['ERP_DB_PATH']; db=sqlite3.connect(p); print('BD:',p); print('Campos:',[r[1] for r in db.execute('PRAGMA table_info(pedidos)')]); assert 'cep' in [r[1] for r in db.execute('PRAGMA table_info(pedidos)')]"
echo "=== Testes ==="
docker compose exec -T erp python -m pytest -q
