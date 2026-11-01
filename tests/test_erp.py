import pytest
from erp.app import create_app

@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3")})
    return app.test_client()

def test_initial_page(client):
    assert b"ERP Demonstrativo" in client.get("/").data

def test_create_and_duplicate(client):
    data = dict(pedido_id="PED-001", cliente="Ana", produto="Mouse", quantidade="2", valor_unitario="30.00", status="pendente")
    client.post("/pedidos", data=data)
    client.post("/pedidos", data=data)
    html = client.get("/").data.decode()
    assert html.count('data-pedido-id="PED-001"') == 1
    assert "Ana" in html

def test_invalid(client):
    client.post("/pedidos", data=dict(pedido_id="X", cliente="A", produto="B", quantidade="-1", valor_unitario="20", status="pendente"))
    assert 'data-pedido-id="X"' not in client.get("/").data.decode()
