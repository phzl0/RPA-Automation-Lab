"""Busca real de pedidos e proteção contra exclusão ambígua."""
import sqlite3
from unittest.mock import patch
import pytest
from erp.app import create_app
from erp.order_lookup import find_orders, resolve_order

@pytest.fixture
def setup(tmp_path):
    app=create_app({"TESTING":True,"DATABASE":str(tmp_path/"erp.sqlite3")})
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute("INSERT INTO pedidos(pedido_id,cliente,produto,quantidade,valor_unitario,status,cep) VALUES (?,?,?,?,?,?,?)",("10","teste 10","Mouse",2,25.0,"pendente",None))
    return app.test_client(),app.config["DATABASE"]

def test_customer_name_resolves_to_real_id(setup):
    _,database=setup
    found=resolve_order(database,{"referencia":"teste 10"})
    assert found["status"]=="resolved"
    assert found["order"]["pedido_id"]=="10"

def test_misinterpreted_name_as_id_can_be_recovered(setup):
    _,database=setup
    found=resolve_order(database,{"pedido_id":"teste 10"})
    assert found["order"]["pedido_id"]=="10"

def test_multiple_matches_require_selection(setup):
    _,database=setup
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO pedidos(pedido_id,cliente,produto,quantidade,valor_unitario,status,cep) VALUES (?,?,?,?,?,?,?)",("11","teste 10","Teclado",1,40.0,"pendente",None))
    found=resolve_order(database,{"referencia":"teste 10"})
    assert found["status"]=="ambiguous"
    assert {r["pedido_id"] for r in found["candidates"]}=={"10","11"}

def test_resolve_endpoint_returns_real_record(setup):
    http,_=setup
    response=http.post("/api/orders/resolve",json={"command":{"action":"excluir_pedido","data":{"referencia":"teste 10"}}})
    assert response.status_code==200
    assert response.get_json()["order"]["pedido_id"]=="10"

def test_delete_refuses_without_selected_snapshot(setup):
    http,_=setup
    with patch("rpa.interactive.run_command") as run:
        response=http.post("/api/rpa/execute",json={"command":{"action":"excluir_pedido","data":{"referencia":"teste 10"}},"confirm":"SIM"})
    assert response.status_code==400
    run.assert_not_called()

def test_delete_rejects_stale_selection(setup):
    http,db_path=setup
    row=find_orders(db_path,"teste 10")[0]
    with sqlite3.connect(db_path) as db:
        db.execute("UPDATE pedidos SET cliente='mudou' WHERE pedido_id='10'")
    with patch("rpa.interactive.run_command") as run:
        response=http.post("/api/rpa/execute",json={"command":{"action":"excluir_pedido","data":{"referencia":"teste 10"}},"selected_order":row,"confirm":"SIM"})
    assert response.status_code==409
    run.assert_not_called()

def test_delete_confirmed_single_match(setup):
    http,db_path=setup
    row=find_orders(db_path,"teste 10")[0]
    with patch("rpa.interactive.run_command",return_value="Pedido excluído") as run:
        response=http.post("/api/rpa/execute",json={"command":{"action":"excluir_pedido","data":{"referencia":"teste 10"}},"selected_order":row,"confirm":"SIM"})
    assert response.status_code==200
    assert run.call_args.args[0]["data"]["pedido_id"]=="10"
