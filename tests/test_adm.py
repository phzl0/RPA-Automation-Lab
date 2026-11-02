import sqlite3
from unittest.mock import patch
import pytest
from erp.app import create_app
from erp.chat_store import get_messages

@pytest.fixture
def client(tmp_path):
    app=create_app({"TESTING":True,"DATABASE":str(tmp_path/"demo.sqlite3")})
    return app.test_client(),app

def test_admin_pages(client):
    http,app=client
    assert http.get("/adm").status_code==200
    assert http.get("/produtos").status_code==200
    assert http.get("/pedidos/lista").status_code==200
    assert b"Chat ADM" in http.get("/controle").data

def test_chat_history_persists(client):
    http,app=client
    ident=http.post("/api/conversations").get_json()["id"]
    with patch("rpa.interpreter.interpret",return_value={"kind":"chat","reply":"Bem-vindo","action":None,"data":{}}):
        response=http.post("/api/chat",json={"conversation_id":ident,"message":"olá"})
    assert response.status_code==200
    messages=http.get(f"/api/conversations/{ident}/messages").get_json()
    assert [m["role"] for m in messages]==["user","model"]
    assert messages[0]["text"]=="olá"
    assert ident in [x["id"] for x in http.get("/api/conversations").get_json()]

def test_rpa_no_write_without_confirmation(client):
    http,app=client
    cmd={"action":"excluir_pedido","data":{"pedido_id":"P-01"}}
    with patch("rpa.interactive.run_command") as execute:
        response=http.post("/api/rpa/execute",json={"command":cmd})
    assert response.status_code==400
    execute.assert_not_called()

def test_rpa_rejects_missing_fields(client):
    http,_=client
    cmd={"action":"criar_pedido","data":{"cliente":"Ana"}}
    with patch("rpa.interactive.run_command") as execute:
        response=http.post("/api/rpa/execute",json={"command":cmd,"confirm":"SIM"})
    assert response.status_code==400
    execute.assert_not_called()

def test_rpa_confirmed_dispatch(client):
    http,_=client
    cmd={"action":"excluir_pedido","data":{"pedido_id":"P-01"}}
    with patch("rpa.interactive.run_command",return_value="Excluído.") as execute:
        response=http.post("/api/rpa/execute",json={"command":cmd,"confirm":"SIM"})
    assert response.status_code==200
    execute.assert_called_once()

def test_manual_product_update_delete(client):
    http,app=client
    http.post("/estoque",data={"sku":"A1","produto":"Mouse","quantidade":"2","preco":"10"})
    http.post("/estoque/editar",data={"sku":"A1","preco":"20"})
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT preco FROM estoque WHERE sku='A1'").fetchone()[0]==20
    http.post("/estoque/excluir",data={"sku":"A1"})
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM estoque WHERE sku='A1'").fetchone()[0]==0
