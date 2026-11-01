"""CLI conversacional com confirmação explícita para ações de escrita."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from rpa.interpreter import interpret, configured_model
from rpa.commands import validate_command, REQUIRED, OPTIONAL, LABELS, FIELDS
from rpa.interactive import run_command

GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"
def say(who, message, color=GREEN):
    print(f"\n{color}{who}{RESET}  {message}", flush=True)

def collect(command):
    action = command["action"]
    data = command["data"]
    say("IA", "Para realizar esta operação, confira os dados abaixo:")
    print("  Obrigatórios: " + ", ".join(LABELS.get(k, k) for k in REQUIRED[action]))
    if OPTIONAL.get(action):
        print("  Opcionais: " + ", ".join(LABELS.get(k, k) for k in OPTIONAL[action]))
    if action == "criar_pedido":
        print("  Status padrão: pendente | CEP vazio: NULL")
    if action == "atualizar_pedido" and command["missing"] == ["campo_para_atualizar"]:
        print("  Informe a alteração em uma nova mensagem, por exemplo: atualize o CEP do pedido P1 para 06454000.")
        return None
    for field in command["missing"]:
        data[field] = input(f"  {LABELS.get(field, field)}: ").strip()
    command = validate_command({"action": action, "data": data})
    if not command["ready"]:
        raise ValueError("Faltam campos obrigatórios.")
    if action == "criar_pedido" and "cep" not in data:
        cep = input("  CEP (opcional; Enter = NULL): ").strip()
        if cep:
            data["cep"] = cep
        command = validate_command({"action": action, "data": data})
    return command

def log_result(command, status, result):
    folder = Path(__file__).resolve().parent.parent / "reports"
    folder.mkdir(exist_ok=True)
    with (folder / "comandos.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"at": datetime.now().isoformat(), "action": command["action"], "data": command["data"], "status": status, "result": result}, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description="RPA Lab — chat e automação de ERP")
    parser.add_argument("message", nargs="*")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    print(f"\n{CYAN}╔════════════════════════════════════════╗")
    print("║    RPA AUTOMATION LAB  ·  GEMINI        ║")
    print(f"╚════════════════════════════════════════╝{RESET}")
    print(f"Modelo: {configured_model()} | /sair encerra | /limpar limpa o contexto")
    history = []
    pending = " ".join(args.message).strip()
    while True:
        try:
            message = pending or input(f"\n{CYAN}Você > {RESET}").strip()
            pending = ""
            if message.lower() in ("/sair", "sair", "exit"):
                print("Até mais!")
                break
            if message.lower() == "/limpar":
                history.clear()
                print("Contexto da conversa limpo.")
                continue
            if not message:
                continue
            print("  ⏳ Consultando Gemini...", flush=True)
            result = interpret(message, history=history)
            reply = str(result.get("reply") or "").strip()
            if result["kind"] == "chat":
                say("IA >", reply or "Como posso ajudar?")
                history.extend([{"role":"user","text":message},{"role":"model","text":reply}])
                continue
            command = validate_command(result)
            say("IA >", reply or "Entendi. Vamos conferir a operação.")
            command = collect(command)
            if command is None:
                continue
            print("\n  Proposta:")
            print(json.dumps(command["data"], ensure_ascii=False, indent=2))
            if command["action"] == "consultar_estoque":
                print("  Consulta sem alteração de dados.")
            elif input("\n  Confirmar execução no navegador? Digite SIM: ").strip() != "SIM":
                say("IA >", "Operação cancelada. Nenhum dado foi alterado.")
                continue
            try:
                output = run_command(command, headless=args.headless)
                say("RPA >", output)
                log_result(command, "sucesso", output)
            except Exception as exc:
                say("RPA >", f"Falha: {exc}")
                log_result(command, "erro", str(exc))
            history.extend([{"role":"user","text":message},{"role":"model","text":reply}])
        except (KeyboardInterrupt, EOFError):
            print("\nConversa encerrada.")
            break
        except Exception as exc:
            say("IA >", f"Não foi possível concluir: {exc.__class__.__name__}: {str(exc)[:250]}")

if __name__ == "__main__":
    main()
