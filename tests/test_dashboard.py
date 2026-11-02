"""Testes do upgrade visual ADM e da origem de auditoria."""
import sqlite3
import pytest
from erp.app import create_app
from erp.metrics import metrics, recent

@pytest.fixture
def env(tmp_path):
    app=create_app({"TESTING": True, "DATABASE":str(tmp_path/"panel.sqlite3")})
    return app.test_client(), app.config["DATABASE"]

def test_all_admin_pages_share_sidebar(env):
    client,_=env
    for path in ("/adm","/pedidos/lista","/produtos","/estoque","/controle","/auditoria","/configuracoes","/pedidos/gerenciar"):
        response=client.get(path)
        assert response.status_code==200, path
        html=response.get_data(as_text=True)
        assert "RPA AUTOMATION" in html and "ADMIN CONSOLE" in html
        assert 'href="/auditoria"' in html
        assert "Administrador" in html
    assert client.get("/").status_code==302
    css=client.get("/static/admin.css")
    assert css.status_code==200
    assert b"--cyan:" in css.data

def test_dashboard_shows_true_kpis_and_activity(env):
    client,db=env
    client.post("/pedidos",data={"pedido_id":"P-009","cliente":"Teste","produto":"Monitor","quantidade":"3","valor_unitario":"50.00","status":"pendente"})
    client.post("/estoque",data={"sku":"S-1","produto":"Monitor","quantidade":"2","preco":"50"})
    overview=metrics(db)
    assert overview["totals"]["orders"]==1
    assert overview["totals"]["products"]==1
    assert overview["totals"]["low_stock"]==1
    assert overview["totals"]["orders_value"]==150
    assert overview["totals"]["manual_actions"]==2
    html=client.get("/adm").get_data(as_text=True)
    assert "150.00" in html
    assert "Monitor" in html
    assert "ADM (manual)" in html
    assert "BRT" in html

def test_manual_updates_and_deletes_tracked(env):
    client,db=env
    client.post("/pedidos",data={"pedido_id":"X","cliente":"Ana","produto":"Teclado","quantidade":"1","valor_unitario":"20","status":"pendente"})
    client.post("/pedidos/atualizar",data={"pedido_id":"X","status":"concluido"})
    client.post("/pedidos/excluir",data={"pedido_id":"X"})
    actions=[item["action"] for item in recent(db)]
    assert "criar_pedido" in actions and "atualizar_pedido" in actions and "excluir_pedido" in actions
    assert all(item["actor_label"]=="ADM (manual)" for item in recent(db))

def test_rpa_header_does_not_fake_manual_actor(env):
    client,db=env
    client.post("/estoque",data={"sku":"RB-1","produto":"Cabo","quantidade":"1","preco":"10"},headers={"X-RPA-Origin":"1"})
    assert metrics(db)["totals"]["manual_actions"]==0
    assert metrics(db)["totals"]["products"]==1

def test_audit_page_has_timestamp_origin_status(env):
    client,_=env
    html=client.get("/auditoria").get_data(as_text=True)
    assert "Horário (Brasília)" in html
    assert "Origem / Quem fez" in html
    assert "Status" in html
