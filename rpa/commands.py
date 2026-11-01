from decimal import Decimal, InvalidOperation

FIELDS = {
    "criar_pedido": ("pedido_id", "cliente", "produto", "quantidade", "valor_unitario", "status"),
    "criar_produto": ("sku", "produto", "quantidade", "preco"),
    "definir_estoque": ("sku", "quantidade"),
    "consultar_estoque": ("sku",),
}
def validate_command(proposal):
    if not isinstance(proposal, dict):
        raise ValueError("Resposta da IA deve ser um objeto.")
    action = proposal.get("action")
    if action not in FIELDS:
        raise ValueError("Operação não reconhecida. Reformule o pedido.")
    raw = proposal.get("data") or {}
    if not isinstance(raw, dict):
        raise ValueError("Dados inválidos.")
    data = {key: str(raw[key]).strip() for key in FIELDS[action] if raw.get(key) is not None}
    if action == "criar_pedido" and not data.get("status"):
        data["status"] = "pendente"
    missing = [key for key in FIELDS[action] if not data.get(key)]
    if not missing:
        for field in ("quantidade",):
            if field in data:
                try:
                    number = int(data[field])
                    if number < 0 or (action == "criar_pedido" and number == 0):
                        raise ValueError()
                    data[field] = str(number)
                except ValueError:
                    raise ValueError("Quantidade deve ser um número inteiro válido.")
        for field in ("preco", "valor_unitario"):
            if field in data:
                try:
                    number = Decimal(data[field].replace(",", "."))
                    if not number.is_finite() or not 0 <= number <= 100000000:
                        raise ValueError()
                    data[field] = f"{number:.2f}"
                except (InvalidOperation, ValueError):
                    raise ValueError("Preço inválido.")
        if data.get("status") not in (None, "pendente", "processando", "concluido"):
            raise ValueError("Status inválido.")
    return {"action": action, "data": data, "missing": missing, "ready": not missing}
