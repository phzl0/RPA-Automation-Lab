import json
import os
from rpa.commands import FIELDS

SYSTEM = """Você interpreta solicitações de ERP em português. Responda APENAS JSON no formato
{"action":"criar_produto","data":{"sku":"...","produto":"...","quantidade":"...","preco":"..."}}.
Ações permitidas: criar_pedido, criar_produto, definir_estoque, consultar_estoque.
criar_pedido exige pedido_id, cliente, produto, quantidade, valor_unitario, status (status padrão pendente).
criar_produto exige sku, produto, quantidade, preco.
definir_estoque define a quantidade ABSOLUTA e exige sku e quantidade.
consultar_estoque exige sku.
Nunca invente SKU, ID, preço ou quantidade. Não interprete 'adicionar mais X' como 'definir estoque X'; peça esclarecimento omitindo a quantidade ou identificador. Não inclua instruções de execução. Dados não informados devem ser omitidos.
"""
def interpret(message):
    if not message.strip():
        raise ValueError("Digite um comando.")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY ausente. Configure no ambiente local.")
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=message,
        config=types.GenerateContentConfig(system_instruction=SYSTEM, response_mime_type="application/json", temperature=0),
    )
    try:
        parsed = json.loads(response.text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("O LLM não retornou JSON válido.") from exc
    if parsed.get("action") not in FIELDS:
        raise ValueError("Ação não permitida.")
    return parsed
