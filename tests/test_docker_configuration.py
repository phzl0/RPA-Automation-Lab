from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_docker_definitions_exist():
    compose = (ROOT / "compose.yaml").read_text()
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "ERP_DB_PATH: /data/erp.sqlite3" in compose
    assert "127.0.0.1:5000:5000" in compose
    assert "python -m playwright install --with-deps chromium" in dockerfile
    assert "python:3.12-slim" in dockerfile

def test_erp_can_bind_all_container_interfaces():
    source = (ROOT / "erp/app.py").read_text()
    assert 'os.getenv("ERP_HOST", "127.0.0.1")' in source
