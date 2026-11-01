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

    @app.get("/")
    def index():
        with connect() as db:
            pedidos = db.execute("SELECT * FROM pedidos ORDER BY pedido_id").fetchall()
        return render_template("index.html", pedidos=pedidos)

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
        if not pedido_id or not changes:
            flash("Informe ID e pelo menos um campo para atualizar.", "error")
            return redirect(url_for("index"))
        sql = "UPDATE pedidos SET " + ", ".join(f"{k}=?" for k in changes) + " WHERE pedido_id=?"
        with connect() as db:
            cursor = db.execute(sql, (*changes.values(), pedido_id))
        flash("Pedido atualizado." if cursor.rowcount else "Pedido não encontrado.", "success" if cursor.rowcount else "error")
        return redirect(url_for("index"))

    @app.get("/estoque")
    def estoque():
        with connect() as db:
            produtos = db.execute("SELECT * FROM estoque ORDER BY sku").fetchall()
        return render_template("estoque.html", produtos=produtos)

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
            flash("Estoque atualizado." if result.rowcount else "SKU não encontrado.", "success" if result.rowcount else "error")
        except (ValueError, OverflowError):
            flash("Quantidade inválida.", "error")
        return redirect(url_for("estoque"))

    @app.get("/controle")
    def controle():
        return render_template("controle.html")

    @app.post("/controle/interpretar")
    def interpretar():
        from rpa.interpreter import interpret
        from rpa.commands import validate_command
        message = str((request.get_json(silent=True) or {}).get("message", ""))[:2000]
        try:
            proposal = interpret(message)
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
    create_app().run(host="127.0.0.1", port=5000, debug=False)
