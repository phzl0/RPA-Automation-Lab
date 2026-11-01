import sqlite3
import pytest
from erp.app import create_app
from rpa.commands import validate_command

@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "orders.sqlite3")})
    return app.test_client(), app

def test_optional_cep_null_and_update(client):
    http, app = client
    http.post("/pedidos", data={"pedido_id":"P1","cliente":"Ana","produto":"Mouse","quantidade":"1","valor_unitario":"20","status":"pendente"})
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT cep FROM pedidos WHERE pedido_id='P1'").fetchone()[0] is None
    http.post("/pedidos/atualizar", data={"pedido_id":"P1","cep":"06454-000"})
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT cep FROM pedidos WHERE pedido_id='P1'").fetchone()[0] == "06454000"
    http.post("/pedidos/atualizar", data={"pedido_id":"P1","limpar_cep":"1"})
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT cep FROM pedidos WHERE pedido_id='P1'").fetchone()[0] is None

def test_command_cep_optional():
    cmd = validate_command({"action":"criar_pedido","data":{"pedido_id":"P2","cliente":"B","produto":"X","quantidade":"1","valor_unitario":"3"}})
    assert cmd["ready"] and "cep" not in cmd["missing"]

def test_update_cep_empty():
    cmd = validate_command({"action":"atualizar_pedido","data":{"pedido_id":"P2","cep":""}})
    assert cmd["ready"] and cmd["data"]["cep"] == ""
