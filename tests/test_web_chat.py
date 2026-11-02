import sqlite3
from erp.app import create_app

def test_greeting_in_web_chat(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "erp.sqlite3")})
    client = app.test_client()
    response = client.post("/controle/interpretar", json={"message": "bom dia", "history": []})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["kind"] == "chat"
    assert "sku" not in str(payload).lower()
    assert "Olá" in payload["reply"]

def test_cep_visible_and_nullable_on_existing_database(tmp_path):
    filename = tmp_path / "erp.sqlite3"
    with sqlite3.connect(filename) as db:
        db.execute("CREATE TABLE pedidos (pedido_id TEXT PRIMARY KEY, cliente TEXT NOT NULL, produto TEXT NOT NULL, quantidade INTEGER NOT NULL, valor_unitario REAL NOT NULL, status TEXT NOT NULL)")
        db.execute("INSERT INTO pedidos VALUES ('ANTIGO','Ana','Mouse',1,20,'pendente')")
    app = create_app({"TESTING": True, "DATABASE": str(filename)})
    client = app.test_client()
    html = client.get("/pedidos/gerenciar").get_data(as_text=True)
    assert 'name="cep"' in html
    assert "<th>CEP</th>" in html
    with sqlite3.connect(filename) as db:
        assert db.execute("SELECT cep FROM pedidos WHERE pedido_id='ANTIGO'").fetchone()[0] is None

def test_web_chat_has_conversational_ui(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "erp.sqlite3")})
    html = app.test_client().get("/controle").get_data(as_text=True)
    assert 'id="chat"' in html
    assert 'JSON.stringify(data,null,2)' not in html
