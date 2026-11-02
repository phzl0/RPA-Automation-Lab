from rpa.commands import validate_command

def test_admin_read_no_extra_fields():
    for action in ("listar_pedidos","listar_produtos","resumo_erp"):
        cmd=validate_command({"action":action,"data":{}})
        assert cmd["ready"] and cmd["missing"]==[]

def test_order_id_generated_but_not_commercial_data():
    cmd=validate_command({"action":"criar_pedido","data":{}})
    assert cmd["data"]["pedido_id"].startswith("PED-")
    assert set(("cliente","produto","quantidade","valor_unitario")) <= set(cmd["missing"])

def test_single_delete_requires_identifier():
    assert not validate_command({"action":"excluir_pedido","data":{}})["ready"]
    assert validate_command({"action":"excluir_pedido","data":{"pedido_id":"P1"}})["ready"]
    assert not validate_command({"action":"excluir_produto","data":{}})["ready"]

def test_partial_product_update():
    cmd=validate_command({"action":"atualizar_produto","data":{"sku":"ABC","preco":"22,50"}})
    assert cmd["ready"] and cmd["data"]["preco"]=="22.50"
