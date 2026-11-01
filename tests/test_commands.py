import pytest
from rpa.commands import validate_command

def test_missing_fields():
    r = validate_command({"action":"criar_produto","data":{"produto":"Mouse"}})
    assert not r["ready"]
    assert set(r["missing"]) == {"sku", "quantidade", "preco"}

def test_valid_stock():
    r = validate_command({"action":"definir_estoque","data":{"sku":"M-01","quantidade":10}})
    assert r["ready"] and r["data"]["quantidade"] == "10"

def test_invalid_quantity():
    with pytest.raises(ValueError):
        validate_command({"action":"definir_estoque","data":{"sku":"M-01","quantidade":-1}})

def test_reject_action():
    with pytest.raises(ValueError):
        validate_command({"action":"delete_all","data":{}})
