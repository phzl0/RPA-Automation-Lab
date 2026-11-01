import argparse
import json
from datetime import datetime
from pathlib import Path
from rpa.interpreter import interpret, configured_model
from rpa.commands import validate_command
from rpa.interactive import run_command

def main():
    parser = argparse.ArgumentParser(description="RPA Lab — CLI em linguagem natural")
    parser.add_argument("message", nargs="*", help="Comando em linguagem natural")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    message = " ".join(args.message).strip() or input("O que deseja fazer? ").strip()
    print(f"Consultando Gemini ({configured_model()}, até 2 tentativas de 15s)...", flush=True)
    try:
        command = validate_command(interpret(message))
    except KeyboardInterrupt:
        print("\nConsulta cancelada pelo usuário.")
        return
    except Exception as exc:
        print(f"Não foi possível interpretar o comando: {exc.__class__.__name__}: {str(exc)[:350]}")
        return
    try:
        while command["missing"]:
            print("Campos faltantes:", ", ".join(command["missing"]))
            for field in command["missing"]:
                command["data"][field] = input(field + ": ").strip()
            command = validate_command(command)
    except (ValueError, KeyboardInterrupt, EOFError) as exc:
        print(f"Cadastro interrompido ou dados inválidos: {exc}")
        return
    print("Proposta:", json.dumps(command, ensure_ascii=False, indent=2))
    if input("Executar via navegador? Digite SIM: ").strip() != "SIM":
        print("Cancelado. Nenhuma ação executada.")
        return
    status = "erro"
    try:
        result = run_command(command, headless=args.headless)
        status = "sucesso"
        print(result)
    except Exception as exc:
        result = str(exc)
        print("Falha:", result)
    finally:
        folder = Path(__file__).resolve().parent.parent / "reports"
        folder.mkdir(exist_ok=True)
        with (folder / "comandos.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps({"at": datetime.now().isoformat(), "action": command["action"], "data": command["data"], "status": status, "result": result}, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
