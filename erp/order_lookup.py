"""Resolução determinística de referências de pedidos no SQLite.

Não assume que o nome do cliente seja um ID. Nunca escolhe automaticamente
entre vários resultados nem executa alterações aqui.
"""
import sqlite3
import unicodedata

def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(ch for ch in value if not unicodedata.combining(ch)).strip()

def find_orders(db_path, reference, limit=20):
    term = normalize(reference)
    if not term or len(term) > 200:
        return []
    with sqlite3.connect(db_path, timeout=10) as db:
        db.row_factory = sqlite3.Row
        records = [dict(r) for r in db.execute(
            "SELECT pedido_id,cliente,produto,quantidade,valor_unitario,status,cep FROM pedidos ORDER BY pedido_id LIMIT 2000"
        )]
    exact = [r for r in records if normalize(r["pedido_id"]) == term or normalize(r["cliente"]) == term]
    if exact:
        return exact[:limit]
    # Somente busca parcial, sem aproximação probabilística ou escolha silenciosa.
    partial = [r for r in records if term in normalize(r["cliente"]) or term in normalize(r["pedido_id"])]
    return partial[:limit]

def get_order(db_path, pedido_id):
    with sqlite3.connect(db_path, timeout=10) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT pedido_id,cliente,produto,quantidade,valor_unitario,status,cep FROM pedidos WHERE pedido_id=?",
            (str(pedido_id),)
        ).fetchone()
    return dict(row) if row else None

def resolve_order(db_path, data):
    """Retorna status: resolved, ambiguous, not_found, missing."""
    ident = str(data.get("pedido_id") or "").strip()
    reference = str(data.get("referencia") or "").strip()
    if ident:
        order = get_order(db_path, ident)
        if order:
            return {"status":"resolved","order":order}
        # Se o modelo confundiu um nome de cliente com ID, tente a busca sem excluir nada.
        if not reference:
            reference = ident
    if not reference:
        return {"status":"missing","candidates":[]}
    matches = find_orders(db_path, reference)
    if len(matches) == 1:
        return {"status":"resolved","order":matches[0]}
    return {"status":"ambiguous" if matches else "not_found","candidates":matches,"reference":reference}
