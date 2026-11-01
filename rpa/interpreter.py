"""Interpretação de comandos de ERP; nenhuma ação é executada pela IA."""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from rpa.commands import FIELDS

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SYSTEM = """Você é um interpretador de comandos para um ERP demonstrativo, não um chatbot.
Responda SOMENTE JSON com as chaves action e data.
Ações permitidas: criar_pedido, criar_produto, definir_estoque, consultar_estoque.
criar_pedido: pedido_id, cliente, produto, quantidade, valor_unitario, status (padrão pendente).
criar_produto: sku, produto, quantidade, preco.
definir_estoque: sku, quantidade ABSOLUTA.
consultar_estoque: sku.
Saudações, conversas, solicitações não relacionadas ou ambiguidades sem ação definida:
{"action":"nenhuma","data":{}}
Nunca invente identificadores, preços, quantidades ou outros dados. Omita campos ausentes.
Nunca transforme 'adicionar mais X unidades' em definição absoluta de estoque.
Não inclua instruções de execução, markdown ou explicações.
"""

def configured_model():
    return os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"

def interpret(message, *, client=None, sleep=time.sleep):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Digite um comando de ERP.")
    if len(message) > 2000:
        raise ValueError("Comando muito longo (máximo 2000 caracteres).")
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if client is None and (not key or key == "coloque_sua_chave_aqui"):
        raise ValueError("GEMINI_API_KEY ausente ou inválida no arquivo .env.")
    from google import genai
    from google.genai import types
    model = configured_model()
    if client is None:
        client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(
                timeout=15000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
    try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=message,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM,
                        response_mime_type="application/json",
                        temperature=0,
                    ),
                )
                break
            except Exception as exc:
                status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                if status is None:
                    status = getattr(exc, "status", None)
                try:
                    status = int(status)
                except (TypeError, ValueError):
                    status = None
                if status in (429, 500, 502, 503, 504) and attempt == 0:
                    sleep(2)
                    continue
                if status == 404:
                    raise RuntimeError(
                        f"Modelo {model!r} indisponível para esta chave. "
                        "Confira GEMINI_MODEL no .env e execute python -m rpa.diagnostico."
                    ) from exc
                if status in (429, 500, 502, 503, 504):
                    raise RuntimeError(
                        f"Gemini indisponível (HTTP {status}) após nova tentativa. "
                        "O ERP não foi alterado; tente mais tarde ou use outro modelo disponível."
                    ) from exc
                if status in (401, 403):
                    raise RuntimeError(
                        f"Gemini recusou a autenticação/permissão (HTTP {status}). "
                        "Confira sua chave e o projeto no Google AI Studio."
                    ) from exc
                if isinstance(exc, (TimeoutError, ConnectionError)) or "timeout" in type(exc).__name__.lower():
                    raise RuntimeError("Tempo limite ao conectar ao Gemini. Confira sua rede e tente novamente.") from exc
                raise
    finally:
        if hasattr(client, "close"):
            client.close()
    try:
        parsed = json.loads(response.text)
    except (TypeError, json.JSONDecodeError, AttributeError) as exc:
        raise ValueError("Gemini não retornou JSON válido.") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Gemini retornou estrutura inválida.")
    if parsed.get("action") == "nenhuma":
        raise ValueError("Não identifiquei uma ação de ERP. Exemplo: 'quero cadastrar um pedido'.")
    if parsed.get("action") not in FIELDS:
        raise ValueError("Ação não permitida ou não reconhecida.")
    return parsed
