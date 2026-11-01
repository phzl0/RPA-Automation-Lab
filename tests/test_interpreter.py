import json
import pytest
from rpa.interpreter import interpret

class Models:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0
    def generate_content(self, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return type("Response", (), {"text": json.dumps(self.response)})()

class Client:
    def __init__(self, models):
        self.models = models
    def close(self):
        pass

def test_valid_command():
    models = Models({"action": "criar_pedido", "data": {}})
    assert interpret("cadastrar pedido", client=Client(models))["action"] == "criar_pedido"

def test_greeting_not_executed():
    models = Models({"action": "nenhuma", "data": {}})
    assert interpret("bom dia", client=Client(models))["kind"] == "chat"

def test_malformed_json_shape():
    models = Models(["criar_pedido"])
    with pytest.raises(ValueError, match="estrutura inválida"):
        interpret("cadastrar pedido", client=Client(models))

def test_no_network_for_empty_command():
    with pytest.raises(ValueError, match="Digite"):
        interpret(" ")
