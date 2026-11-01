"""Diagnóstico sem revelar credenciais nem executar ações no ERP."""
import os
from dotenv import load_dotenv
from rpa.interpreter import ROOT, configured_model

def main():
    load_dotenv(ROOT / ".env")
    key = os.getenv("GEMINI_API_KEY", "").strip()
    print("Arquivo .env:", "encontrado" if (ROOT / ".env").is_file() else "ausente")
    print("GEMINI_API_KEY:", "configurada" if key and key != "coloque_sua_chave_aqui" else "ausente/inválida")
    print("Modelo configurado:", configured_model())
    if not key or key == "coloque_sua_chave_aqui":
        return
    from google import genai
    from google.genai import types
    try:
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=12000, retry_options=types.HttpRetryOptions(attempts=1)))
        try:
            models = list(client.models.list())
            names = [m.name for m in models if "generateContent" in (getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None) or [])]
            if not names:
                names = [m.name for m in models]
            print("Modelos disponíveis (lista retornada pela API):")
            for name in names:
                print(" -", name)
            configured = configured_model()
            print("Modelo configurado encontrado na lista:", any(n == configured or n == "models/" + configured for n in names))
        finally:
            client.close()
    except Exception as exc:
        print("Falha na consulta de modelos:", type(exc).__name__, str(exc)[:300])

if __name__ == "__main__":
    main()
