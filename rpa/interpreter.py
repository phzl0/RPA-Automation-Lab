"""Gemini responde conversas e propõe ações; nunca executa RPA."""
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from rpa.commands import FIELDS

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
SYSTEM = """Você é um assistente conversacional amigável em português brasileiro.
Responda perguntas gerais normalmente. Quando o usuário desejar uma ação no ERP, retorne uma proposta estruturada.
Responda SEMPRE JSON com as chaves kind, reply, action, data.
Para conversa normal: {"kind":"chat","reply":"sua resposta natural","action":null,"data":{}}.
Para operações ERP: {"kind":"rpa","reply":"mensagem breve e acolhedora","action":"criar_pedido","data":{}}.
Ações permitidas: criar_pedido, atualizar_pedido, criar_produto, definir_estoque, consultar_estoque.
criar_pedido: pedido_id, cliente, produto, quantidade, valor_unitario, status, cep.
atualizar_pedido: pedido_id e APENAS os campos que o usuário quer alterar; cep vazio significa limpar para NULL.
criar_produto: sku, produto, quantidade, preco.
definir_estoque: sku, quantidade ABSOLUTA.
consultar_estoque: sku.
Nunca invente IDs, preços, quantidades, CEPs ou outros dados. Omita dados não informados.
Não trate saudações ou perguntas comuns como comandos ERP. Não inclua markdown, ações executadas ou confirmação falsa.
"""
def configured_model():
    return os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip() or "gemini-3.5-flash-lite"

def interpret(message, *, history=None, client=None, sleep=time.sleep):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Digite uma mensagem.")
    if len(message) > 4000:
        raise ValueError("Mensagem muito longa.")
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if client is None and (not key or key == "coloque_sua_chave_aqui"):
        raise ValueError("Configure GEMINI_API_KEY no .env.")
    from google import genai
    from google.genai import types
    if client is None:
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=15000, retry_options=types.HttpRetryOptions(attempts=1)))
    contents = []
    for entry in (history or [])[-10:]:
        if entry.get("role") in ("user", "model") and isinstance(entry.get("text"), str):
            contents.append(types.Content(role=entry["role"], parts=[types.Part.from_text(text=entry["text"][:2000])]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
    try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=configured_model(), contents=contents,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM, response_mime_type="application/json", temperature=0.2),
                )
                break
            except Exception as exc:
                status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                try: status = int(status)
                except (ValueError, TypeError): status = None
                if status in (429, 500, 502, 503, 504) and attempt == 0:
                    sleep(1)
                    continue
                if status == 404:
                    raise RuntimeError(f"Modelo {configured_model()} indisponível. Execute python -m rpa.diagnostico.") from exc
                if status in (429, 500, 502, 503, 504):
                    raise RuntimeError(f"Gemini indisponível (HTTP {status}); tente novamente depois.") from exc
                if status in (401, 403):
                    raise RuntimeError(f"Gemini recusou chave ou permissão (HTTP {status}).") from exc
                if "timeout" in type(exc).__name__.lower():
                    raise RuntimeError("Tempo limite de conexão com Gemini.") from exc
                raise
    finally:
        if hasattr(client, "close"):
            client.close()
    try:
        result = json.loads(response.text)
    except (TypeError, ValueError) as exc:
        raise ValueError("Resposta do Gemini não é JSON válido.") from exc
    if not isinstance(result, dict):
        raise ValueError("Resposta inválida do Gemini.")
    # Compatibilidade com respostas de testes/versões anteriores.
    if "kind" not in result:
        result["kind"] = "rpa" if result.get("action") in FIELDS else "chat"
    if result["kind"] == "rpa" and result.get("action") not in FIELDS:
        raise ValueError("Ação de ERP não permitida.")
    if result["kind"] not in ("chat", "rpa"):
        raise ValueError("Tipo de resposta inválido.")
    result.setdefault("reply", "")
    result.setdefault("data", {})
    return result
