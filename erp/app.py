import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

BASE = Path(__file__).resolve().parent.parent
DB = Path(os.getenv("ERP_DB_PATH", str(BASE / "erp.sqlite3")))

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "local-demo-only"), DATABASE=str(DB))
    if test_config:
        app.config.update(test_config)

    def connect():
        db = sqlite3.connect(app.config["DATABASE"], timeout=10)
        db.row_factory = sqlite3.Row
        return db

    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS pedidos (
            pedido_id TEXT PRIMARY KEY, cliente TEXT NOT NULL, produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL CHECK(quantidade > 0),
            valor_unitario REAL NOT NULL CHECK(valor_unitario >= 0),
            status TEXT NOT NULL CHECK(status IN ('pendente','processando','concluido')), cep TEXT NULL)""")
        cols = {row[1] for row in db.execute("PRAGMA table_info(pedidos)")}
        if "cep" not in cols:
            db.execute("ALTER TABLE pedidos ADD COLUMN cep TEXT NULL")
        db.execute("""CREATE TABLE IF NOT EXISTS estoque (
            sku TEXT PRIMARY KEY, produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL CHECK(quantidade >= 0),
            preco REAL NOT NULL CHECK(preco >= 0 AND preco <= 100000000))""")

    from erp.metrics import initialize as init_activity, record as record_activity
    init_activity(app.config["DATABASE"])

    def track(action, kind, ident, detail="", changed=True):
        if changed and request.headers.get("X-RPA-Origin") != "1":
            record_activity(app.config["DATABASE"], action, kind, ident, detail)

    from erp.chat_store import init_chat
    from erp.adm_routes import adm
    init_chat(app.config["DATABASE"])
    app.register_blueprint(adm)

    @app.get("/")
    def home():
        return redirect(url_for("adm.dashboard"))

    @app.get("/pedidos/gerenciar")
    def index():
        with connect() as db:
            pedidos = db.execute("SELECT * FROM pedidos ORDER BY pedido_id").fetchall()
        return render_template("index.html", pedidos=pedidos, section="cadastro", page_name="Gerenciar pedidos")

    @app.post("/pedidos")
    def cadastrar():
        pedido_id = request.form.get("pedido_id", "").strip()
        cliente = request.form.get("cliente", "").strip()
        produto = request.form.get("produto", "").strip()
        status = request.form.get("status", "pendente").strip()
        cep = request.form.get("cep", "").strip().replace("-", "")
        try:
            quantidade = int(request.form.get("quantidade", ""))
            valor = float(request.form.get("valor_unitario", ""))
            if not pedido_id or not cliente or not produto or quantidade <= 0 or not 0 <= valor <= 100000000 or (status not in ("pendente", "processando", "concluido") or (cep and (len(cep) != 8 or not cep.isdigit()))):
                raise ValueError("Dados inválidos")
            with connect() as db:
                db.execute("INSERT INTO pedidos (pedido_id,cliente,produto,quantidade,valor_unitario,status,cep) VALUES (?,?,?,?,?,?,?)", (pedido_id, cliente, produto, quantidade, valor, status, cep or None))
            track("criar_pedido", "pedido", pedido_id, "Cliente: " + cliente)
            flash("Pedido cadastrado com sucesso.", "success")
        except sqlite3.IntegrityError:
            flash("Pedido já cadastrado ou dados inválidos.", "error")
        except (ValueError, OverflowError):
            flash("Verifique os campos informados.", "error")
        return redirect(url_for("index"))

    @app.post("/pedidos/atualizar")
    def atualizar_pedido():
        pedido_id = request.form.get("pedido_id", "").strip()
        changes = {}
        for field in ("cliente", "produto", "quantidade", "valor_unitario", "status", "cep"):
            if field not in request.form:
                continue
            value = request.form[field].strip()
            if not value:
                continue
            if field == "cep":
                value = value.replace("-", "") or None
                if value is not None and (len(value) != 8 or not value.isdigit()):
                    flash("CEP inválido.", "error")
                    return redirect(url_for("index"))
            elif field == "quantidade":
                try:
                    value = int(value)
                    if value <= 0: raise ValueError()
                except ValueError:
                    flash("Quantidade inválida.", "error")
                    return redirect(url_for("index"))
            elif field == "valor_unitario":
                try:
                    value = float(value)
                    if not 0 <= value <= 100000000: raise ValueError()
                except (ValueError, OverflowError):
                    flash("Valor inválido.", "error")
                    return redirect(url_for("index"))
            elif field == "status":
                if value not in ("pendente", "processando", "concluido"):
                    flash("Status inválido.", "error")
                    return redirect(url_for("index"))
            elif not value:
                flash("Campo obrigatório não pode ficar vazio.", "error")
                return redirect(url_for("index"))
            changes[field] = value
        if request.form.get("limpar_cep") == "1":
            changes["cep"] = None
        if not pedido_id or not changes:
            flash("Informe ID e pelo menos um campo para atualizar.", "error")
            return redirect(url_for("index"))
        sql = "UPDATE pedidos SET " + ", ".join(f"{k}=?" for k in changes) + " WHERE pedido_id=?"
        with connect() as db:
            cursor = db.execute(sql, (*changes.values(), pedido_id))
        track("atualizar_pedido", "pedido", pedido_id, "Campos: " + ", ".join(changes), bool(cursor.rowcount))
        flash("Pedido atualizado." if cursor.rowcount else "Pedido não encontrado.", "success" if cursor.rowcount else "error")
        return redirect(url_for("index"))

    @app.get("/estoque")
    def estoque():
        with connect() as db:
            produtos = db.execute("SELECT * FROM estoque ORDER BY sku").fetchall()
        return render_template("estoque.html", produtos=produtos, section="estoque", page_name="Estoque")

    @app.post("/estoque")
    def cadastrar_produto():
        sku = request.form.get("sku", "").strip()
        produto = request.form.get("produto", "").strip()
        try:
            quantidade = int(request.form.get("quantidade", ""))
            preco = float(request.form.get("preco", ""))
            if not sku or not produto or quantidade < 0 or not 0 <= preco <= 100000000:
                raise ValueError()
            with connect() as db:
                db.execute("INSERT INTO estoque VALUES (?,?,?,?)", (sku, produto, quantidade, preco))
            track("criar_produto", "produto", sku, "Produto: " + produto)
            flash("Produto cadastrado.", "success")
        except sqlite3.IntegrityError:
            flash("SKU já cadastrado.", "error")
        except (ValueError, OverflowError):
            flash("Dados de produto inválidos.", "error")
        return redirect(url_for("estoque"))

    @app.post("/estoque/atualizar")
    def atualizar_estoque():
        sku = request.form.get("sku", "").strip()
        try:
            quantidade = int(request.form.get("quantidade", ""))
            if quantidade < 0:
                raise ValueError()
            with connect() as db:
                result = db.execute("UPDATE estoque SET quantidade=? WHERE sku=?", (quantidade, sku))
            track("definir_estoque", "produto", sku, "Quantidade: " + str(quantidade), bool(result.rowcount))
            flash("Estoque atualizado." if result.rowcount else "SKU não encontrado.", "success" if result.rowcount else "error")
        except (ValueError, OverflowError):
            flash("Quantidade inválida.", "error")
        return redirect(url_for("estoque"))

    @app.post("/pedidos/excluir")
    def excluir_pedido():
        ident=request.form.get("pedido_id","").strip()
        if not ident:
            flash("Informe o ID do pedido.","error")
            return redirect(url_for("index"))
        with connect() as db:
            changed=db.execute("DELETE FROM pedidos WHERE pedido_id=?",(ident,)).rowcount
        track("excluir_pedido", "pedido", ident, "Exclusão manual", bool(changed))
        flash("Pedido excluído." if changed else "Pedido não encontrado.","success" if changed else "error")
        return redirect(url_for("index"))

    @app.post("/estoque/editar")
    def editar_produto():
        sku=request.form.get("sku","").strip()
        changes={}
        for field in ("produto","quantidade","preco"):
            if field not in request.form or not request.form[field].strip():
                continue
            value=request.form[field].strip()
            try:
                if field=="quantidade":
                    value=int(value)
                    if value<0: raise ValueError()
                elif field=="preco":
                    value=float(value)
                    if not 0<=value<=100000000: raise ValueError()
            except (ValueError,OverflowError):
                flash("Valores inválidos.","error")
                return redirect(url_for("estoque"))
            changes[field]=value
        if not sku or not changes:
            flash("Informe SKU e pelo menos uma alteração.","error")
            return redirect(url_for("estoque"))
        with connect() as db:
            changed=db.execute("UPDATE estoque SET "+",".join(k+"=?" for k in changes)+" WHERE sku=?",(*changes.values(),sku)).rowcount
        track("atualizar_produto", "produto", sku, "Campos: " + ", ".join(changes), bool(changed))
        flash("Produto atualizado." if changed else "SKU não encontrado.","success" if changed else "error")
        return redirect(url_for("estoque"))

    @app.post("/estoque/excluir")
    def excluir_produto():
        sku=request.form.get("sku","").strip()
        if not sku:
            flash("Informe o SKU.","error")
            return redirect(url_for("estoque"))
        with connect() as db:
            changed=db.execute("DELETE FROM estoque WHERE sku=?",(sku,)).rowcount
        track("excluir_produto", "produto", sku, "Exclusão manual", bool(changed))
        flash("Produto excluído." if changed else "SKU não encontrado.","success" if changed else "error")
        return redirect(url_for("estoque"))

    @app.get("/controle")
    def controle():
        return render_template("controle.html", section="chat", page_name="Chat ADM")

    @app.post("/controle/interpretar")
    def interpretar():
        from rpa.interpreter import interpret
        from rpa.commands import validate_command
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", ""))[:4000]
        history = payload.get("history", [])
        if not isinstance(history, list):
            history = []
        history = [x for x in history[-10:] if isinstance(x, dict) and x.get("role") in ("user", "model") and isinstance(x.get("text"), str)]
        try:
            proposal = interpret(message, history=history)
            if proposal["kind"] == "chat":
                return jsonify({"kind": "chat", "reply": proposal["reply"]})
            validated = validate_command(proposal)
            return jsonify({"kind": "rpa", "reply": proposal["reply"], "command": validated})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

    # Executions are deliberately NOT exposed as HTTP API endpoints.
    # The CLI runs Playwright; the chat UI provides interpretation and a CLI command to copy.
    return app

if __name__ == "__main__":
    create_app().run(host=os.getenv("ERP_HOST", "127.0.0.1"), port=5000, debug=False)
