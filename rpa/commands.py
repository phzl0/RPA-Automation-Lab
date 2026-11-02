from decimal import Decimal, InvalidOperation
from uuid import uuid4

FIELDS = {
    "criar_pedido": ("pedido_id", "cliente", "produto", "quantidade", "valor_unitario", "status", "cep"),
    "atualizar_pedido": ("pedido_id", "cliente", "produto", "quantidade", "valor_unitario", "status", "cep"),
    "criar_produto": ("sku", "produto", "quantidade", "preco"),
    "definir_estoque": ("sku", "quantidade"),
    "consultar_estoque": ("sku",),
    "listar_pedidos": (),
    "listar_produtos": (),
    "resumo_erp": (),
    "excluir_pedido": ("pedido_id", "referencia"),
    "excluir_produto": ("sku",),
    "atualizar_produto": ("sku", "produto", "quantidade", "preco"),
}
REQUIRED = {
    "criar_pedido": ("pedido_id", "cliente", "produto", "quantidade", "valor_unitario"),
    "atualizar_pedido": ("pedido_id",),
    "criar_produto": ("sku", "produto", "quantidade", "preco"),
    "definir_estoque": ("sku", "quantidade"),
    "consultar_estoque": ("sku",),
    "listar_pedidos": (),
    "listar_produtos": (),
    "resumo_erp": (),
    "excluir_pedido": (),
    "excluir_produto": ("sku",),
    "atualizar_produto": ("sku",),
}
OPTIONAL = {
    "criar_pedido": ("status", "cep"),
    "atualizar_pedido": ("cliente", "produto", "quantidade", "valor_unitario", "status", "cep"),
    "atualizar_produto": ("produto", "quantidade", "preco"),
}
LABELS = {"pedido_id":"ID do pedido","cliente":"Cliente","produto":"Produto","quantidade":"Quantidade","valor_unitario":"Valor unitário (R$)","status":"Status","referencia":"Referência de pedido/cliente","cep":"CEP","sku":"SKU","preco":"Preço (R$)"}

def validate_command(proposal):
    if not isinstance(proposal, dict):
        raise ValueError("Resposta da IA deve ser um objeto.")
    action = proposal.get("action")
    if action not in FIELDS:
        raise ValueError("Operação não reconhecida.")
    raw = proposal.get("data") or {}
    if not isinstance(raw, dict):
        raise ValueError("Dados inválidos.")
    data = {key: str(raw[key]).strip() for key in FIELDS[action] if raw.get(key) is not None}
    if action == "excluir_pedido" and not (data.get("pedido_id") or data.get("referencia")):
        return {"action":action,"data":data,"missing":["referencia"],"ready":False}
    if action == "criar_pedido" and not data.get("pedido_id"):
        data["pedido_id"] = "PED-" + uuid4().hex[:10].upper()
    if action == "criar_pedido" and not data.get("status"):
        data["status"] = "pendente"
    if action in ("atualizar_pedido", "atualizar_produto") and not any(k in data for k in FIELDS[action] if k != ("pedido_id" if action == "atualizar_pedido" else "sku")):
        missing = ["campo_para_atualizar"]
    else:
        missing = [key for key in REQUIRED[action] if not data.get(key)]
    if "quantidade" in data and data["quantidade"]:
        try:
            n = int(data["quantidade"])
            if n < 0 or (action in ("criar_pedido", "atualizar_pedido") and n == 0):
                raise ValueError()
            data["quantidade"] = str(n)
        except ValueError as exc:
            raise ValueError("Quantidade deve ser um inteiro válido.") from exc
    for field in ("preco", "valor_unitario"):
        if field in data and data[field]:
            try:
                n = Decimal(data[field].replace(",", "."))
                if not n.is_finite() or not 0 <= n <= 100000000:
                    raise ValueError()
                data[field] = f"{n:.2f}"
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("Preço inválido.") from exc
    if data.get("status") and data["status"] not in ("pendente", "processando", "concluido"):
        raise ValueError("Status inválido.")
    if "cep" in data:
        cep = "".join(ch for ch in data["cep"] if ch.isdigit())
        if data["cep"] and (len(cep) != 8 or any(ch not in "0123456789-" for ch in data["cep"])):
            raise ValueError("CEP deve conter 8 dígitos.")
        data["cep"] = cep if cep else ""
    return {"action": action, "data": data, "missing": missing, "ready": not missing}
