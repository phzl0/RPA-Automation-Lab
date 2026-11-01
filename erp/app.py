import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

BASE = Path(__file__).resolve().parent.parent
DB = Path(os.getenv("ERP_DB_PATH", str(BASE / "erp.sqlite3")))

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "local-demo-only"), DATABASE=str(DB))
    if test_config:
        app.config.update(test_config)
    def connect():
        db = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        return db
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS pedidos (
            pedido_id TEXT PRIMARY KEY, cliente TEXT NOT NULL, produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL CHECK(quantidade > 0),
            valor_unitario REAL NOT NULL CHECK(valor_unitario >= 0),
            status TEXT NOT NULL CHECK(status IN ('pendente','processando','concluido'))
        )""")
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
        try:
            quantidade = int(request.form.get("quantidade", ""))
            valor = float(request.form.get("valor_unitario", ""))
            if not pedido_id or not cliente or not produto or quantidade <= 0 or not 0 <= valor <= 100000000 or status not in ("pendente", "processando", "concluido"):
                raise ValueError("Dados inválidos")
            with connect() as db:
                db.execute("INSERT INTO pedidos VALUES (?,?,?,?,?,?)", (pedido_id, cliente, produto, quantidade, valor, status))
            flash("Pedido cadastrado com sucesso.", "success")
        except sqlite3.IntegrityError:
            flash("Pedido já cadastrado ou dados inválidos.", "error")
        except (ValueError, OverflowError):
            flash("Verifique os campos informados.", "error")
        return redirect(url_for("index"))
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
