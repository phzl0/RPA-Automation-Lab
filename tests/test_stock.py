import pytest
from erp.app import create_app

@pytest.fixture
def client(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "stock.sqlite3")}).test_client()

def test_stock_create_update(client):
    client.post("/estoque", data={"sku":"M-01","produto":"Mouse","quantidade":"20","preco":"49.90"})
    client.post("/estoque/atualizar", data={"sku":"M-01","quantidade":"30"})
    html = client.get("/estoque").data.decode()
    assert html.count('data-sku="M-01"') == 1
    assert ">30</td>" in html

def test_stock_negative_blocked(client):
    client.post("/estoque", data={"sku":"X","produto":"Bad","quantidade":"-2","preco":"10"})
    assert 'data-sku="X"' not in client.get("/estoque").data.decode()
