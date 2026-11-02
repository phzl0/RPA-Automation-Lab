"""Rotas administrativas. Laboratório local, sem autenticação."""
from flask import Blueprint, current_app, jsonify, render_template, request
import os
from erp.chat_store import new_conversation, list_conversations, get_messages, save_message, delete_conversation, audit
from erp.adm import rows, overview
from erp.metrics import metrics, recent
from erp.order_lookup import resolve_order, get_order

adm = Blueprint("adm", __name__)

def path():
    return current_app.config["DATABASE"]

@adm.get("/adm")
def dashboard():
    return render_template("adm.html", data=metrics(path()), section="dashboard", page_name="Dashboard")

@adm.get("/pedidos/lista")
def order_list():
    return render_template("lista.html", heading="Pedidos", section="pedidos", fields=("pedido_id","cliente","produto","quantidade","valor_unitario","status","cep"), records=rows(path(),"pedidos"), page_name="Pedidos")

@adm.get("/produtos")
def product_list():
    return render_template("lista.html", heading="Produtos", section="produtos", fields=("sku","produto","quantidade","preco"), records=rows(path(),"estoque"), page_name="Produtos")


@adm.get("/configuracoes")
def settings_page():
    from rpa.interpreter import configured_model
    return render_template("configuracoes.html", section="configuracoes", page_name="Configurações",
                           model=configured_model(), db_name=os.path.basename(path()))

@adm.get("/auditoria")
def audit_page():
    return render_template("auditoria.html", events=recent(path(), 100),
                           section="auditoria", page_name="Auditoria")

@adm.get("/api/conversations")
def conversations():
    return jsonify(list_conversations(path()))

@adm.post("/api/conversations")
def create_conversation():
    return jsonify({"id":new_conversation(path())}),201

@adm.get("/api/conversations/<ident>/messages")
def conversation_messages(ident):
    try:
        return jsonify(get_messages(path(), ident))
    except ValueError as exc:
        return jsonify({"error":str(exc)}),404

@adm.delete("/api/conversations/<ident>")
def conversation_delete(ident):
    delete_conversation(path(), ident)
    return jsonify({"deleted":True})

@adm.post("/api/chat")
def chat():
    from rpa.interpreter import interpret
    from rpa.commands import validate_command
    payload=request.get_json(silent=True) or {}
    message=str(payload.get("message","")).strip()[:4000]
    ident=str(payload.get("conversation_id") or "")
    if not message:
        return jsonify({"error":"Mensagem vazia."}),400
    try:
        if not ident:
            ident=new_conversation(path())
        history=[{"role":m["role"],"text":m["text"]} for m in get_messages(path(),ident,12) if m["role"] in ("user","model")]
        proposal=interpret(message,history=history)
        reply=str(proposal.get("reply") or "")
        result={"kind":proposal["kind"],"reply":reply,"conversation_id":ident}
        if proposal["kind"]=="rpa":
            command=validate_command(proposal)
            result["command"]=command
            if command["ready"]:
                if command["action"]=="resumo_erp":
                    result["result"]=overview(path())
                elif command["action"] in ("listar_pedidos","listar_produtos"):
                    result["result"]=rows(path(),"pedidos" if command["action"]=="listar_pedidos" else "estoque")
        save_message(path(),ident,"user",message)
        save_message(path(),ident,"model",reply)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error":str(exc)}),400
    except Exception as exc:
        return jsonify({"error":str(exc)[:250]}),503

@adm.post("/api/orders/resolve")
def resolve_order_route():
    from rpa.commands import validate_command
    payload=request.get_json(silent=True) or {}
    command=validate_command(payload.get("command"))
    if command["action"]!="excluir_pedido":
        return jsonify({"error":"Esta busca atende à exclusão de pedido."}),400
    resolution=resolve_order(path(), command["data"])
    return jsonify(resolution)

@adm.post("/api/rpa/execute")
def execute():
    from rpa.commands import validate_command
    from rpa.interactive import run_command
    payload=request.get_json(silent=True) or {}
    ident=str(payload.get("conversation_id") or "")
    command=None
    try:
        command=validate_command(payload.get("command"))
        if not command["ready"]:
            return jsonify({"error":"Faltam dados obrigatórios.","missing":command["missing"]}),400
        action=command["action"]
        allowed=("criar_pedido","atualizar_pedido","excluir_pedido","criar_produto","atualizar_produto","excluir_produto","definir_estoque","consultar_estoque")
        if action not in allowed:
            return jsonify({"error":"Operação não autorizada."}),400
        if action=="excluir_pedido":
            # Em cada execução, revalide o pedido escolhido contra o banco real.
            chosen=payload.get("selected_order")
            if not isinstance(chosen,dict) or not chosen.get("pedido_id"):
                return jsonify({"error":"Selecione e revise o pedido identificado antes de excluir."}),400
            current=get_order(path(),chosen["pedido_id"])
            if not current or any(current.get(k)!=chosen.get(k) for k in current):
                return jsonify({"error":"Pedido não encontrado ou alterado desde a confirmação. Pesquise novamente."}),409
            resolution=resolve_order(path(),command["data"])
            candidates=[resolution["order"]] if resolution["status"]=="resolved" else resolution.get("candidates",[])
            if not any(item["pedido_id"]==current["pedido_id"] for item in candidates):
                return jsonify({"error":"Pedido selecionado não corresponde à referência pesquisada."}),409
            command=validate_command({"action":"excluir_pedido","data":{"pedido_id":current["pedido_id"]}})
        if action != "consultar_estoque" and payload.get("confirm")!="SIM":
            return jsonify({"error":"Confirmação SIM obrigatória."}),400
        result=run_command(command,headless=True)
        audit(path(),ident or None,action,command["data"],"sucesso",result)
        if ident:
            save_message(path(),ident,"system","RPA: "+result)
        return jsonify({"result":result})
    except Exception as exc:
        audit(path(),ident or None,(command or {}).get("action","erro"),(command or {}).get("data",{}),"erro",str(exc))
        return jsonify({"error":str(exc)[:250]}),400
