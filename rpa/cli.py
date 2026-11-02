"""CLI ADM: conversas persistentes em SQLite e execução RPA controlada."""
import argparse
import json
import os
from pathlib import Path
from rpa.interpreter import interpret, configured_model
from rpa.commands import validate_command, REQUIRED, OPTIONAL, LABELS
from rpa.interactive import run_command
from erp.chat_store import init_chat, new_conversation, list_conversations, get_messages, save_message, audit
from erp.adm import rows, overview

def say(label,text):
    print("\n" + label + "  " + str(text),flush=True)

def main():
    parser=argparse.ArgumentParser(description="Chat ADM com histórico persistente")
    parser.add_argument("message",nargs="*")
    parser.add_argument("--headless",action="store_true")
    args=parser.parse_args()
    db_path=os.getenv("ERP_DB_PATH",str(Path(__file__).resolve().parent.parent/"erp.sqlite3"))
    init_chat(db_path)
    print("\n"+"="*54+"\n RPA AUTOMATION LAB · CHAT ADM \n"+"="*54)
    print("⚠ LABORATÓRIO SEM LOGIN. IA pode propor cadastros, alterações e exclusões.")
    print("⚠ Utilize dados fictícios; confirme cada gravação; exclusões são permanentes.")
    print("⚠ Campos indispensáveis nunca devem ser inventados pelo modelo.")
    print("Modelo:",configured_model(),"| /nova | /historico | /sair")
    saved=list_conversations(db_path)
    if saved:
        print("\nConversas recentes:")
        for i,conv in enumerate(saved[:10],1):
            print(f" {i}. {conv['title']}")
        choice=input("Escolha número para continuar ou Enter para nova: ").strip()
        ident=saved[int(choice)-1]["id"] if choice.isdigit() and 1<=int(choice)<=min(len(saved),10) else new_conversation(db_path)
    else:
        ident=new_conversation(db_path)
    history=[{"role":m["role"],"text":m["text"]} for m in get_messages(db_path,ident,10) if m["role"] in ("user","model")]
    pending=" ".join(args.message).strip()
    while True:
        try:
            message=pending or input("\nVocê > ").strip()
            pending=""
            if message.lower() in ("/sair","sair","exit"):
                break
            if message.lower()=="/nova":
                ident=new_conversation(db_path)
                history=[]
                say("Sistema >","Nova conversa salva.")
                continue
            if message.lower()=="/historico":
                for m in get_messages(db_path,ident,40):
                    say(m["role"],m["text"])
                continue
            if not message:
                continue
            print("  ⏳ Interpretando...",flush=True)
            result=interpret(message,history=history)
            reply=str(result.get("reply") or "")
            save_message(db_path,ident,"user",message)
            say("IA >",reply)
            if result["kind"]=="chat":
                save_message(db_path,ident,"model",reply)
                history.extend([{"role":"user","text":message},{"role":"model","text":reply}])
                history=history[-10:]
                continue
            command=validate_command(result)
            action=command["action"]
            if action in ("resumo_erp","listar_pedidos","listar_produtos") and command["ready"]:
                payload=overview(db_path) if action=="resumo_erp" else rows(db_path,"pedidos" if action=="listar_pedidos" else "estoque")
                say("ERP >",json.dumps(payload,ensure_ascii=False,indent=2))
                save_message(db_path,ident,"model",reply+"\n"+json.dumps(payload,ensure_ascii=False))
                history.extend([{"role":"user","text":message},{"role":"model","text":reply}])
                history=history[-10:]
                continue
            if not command["ready"]:
                print("Obrigatórios:",", ".join(LABELS.get(k,k) for k in REQUIRED[action]))
                if OPTIONAL.get(action):
                    print("Opcionais:",", ".join(LABELS.get(k,k) for k in OPTIONAL[action]))
                for field in command["missing"]:
                    if field=="campo_para_atualizar":
                        print("Diga em outra mensagem qual campo alterar.")
                        break
                    command["data"][field]=input(LABELS.get(field,field)+": ").strip()
                command=validate_command(command)
            if not command["ready"]:
                say("Sistema >","Dados insuficientes. Nenhuma ação executada.")
                save_message(db_path,ident,"model",reply+" (dados insuficientes)")
                continue
            if action=="criar_pedido" and "cep" not in command["data"]:
                cep=input("CEP opcional (Enter = NULL): ").strip()
                if cep:
                    command["data"]["cep"]=cep
                    command=validate_command(command)
            print("Proposta:",json.dumps(command,ensure_ascii=False,indent=2))
            if action!="consultar_estoque" and input("Confirmar alteração no ERP? Digite SIM: ").strip()!="SIM":
                say("Sistema >","Operação cancelada.")
                save_message(db_path,ident,"model",reply+" (cancelado)")
                continue
            try:
                output=run_command(command,headless=args.headless or os.getenv("RPA_HEADLESS")=="1")
                say("RPA >",output)
                audit(db_path,ident,action,command["data"],"sucesso",output)
                save_message(db_path,ident,"system","RPA: "+output)
            except Exception as exc:
                say("RPA >","Erro: "+str(exc))
                audit(db_path,ident,action,command["data"],"erro",str(exc))
            save_message(db_path,ident,"model",reply)
            history.extend([{"role":"user","text":message},{"role":"model","text":reply}])
            history=history[-10:]
        except (KeyboardInterrupt,EOFError):
            break
        except Exception as exc:
            say("Sistema >",f"{type(exc).__name__}: {str(exc)[:250]}")
    print("Conversa preservada no banco local.")

if __name__=="__main__":
    main()
