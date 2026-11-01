import pytest
from rpa.robot import validate, load_orders

def test_csv():
    assert len(load_orders("data/pedidos_exemplo.csv")) == 3

def test_validate():
    row = dict(pedido_id="1", cliente="A", produto="B", quantidade="2", valor_unitario="1.50", status="pendente")
    assert validate(row)["quantidade"] == "2"
    row["quantidade"] = "0"
    with pytest.raises(ValueError):
        validate(row)
