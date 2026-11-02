"""Consultas e mutações do ERP ADM. Apenas acesso a banco local demonstrativo."""
import sqlite3

def rows(db_path, table, limit=100):
    if table not in ("pedidos","estoque"):
        raise ValueError("Tabela não autorizada.")
    with sqlite3.connect(db_path) as db:
        db.row_factory=sqlite3.Row
        return [dict(r) for r in db.execute(f"SELECT * FROM {table} ORDER BY 1 LIMIT ?",(min(limit,500),))]

def overview(db_path):
    with sqlite3.connect(db_path) as db:
        pedidos=db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        produtos=db.execute("SELECT COUNT(*) FROM estoque").fetchone()[0]
        valor=db.execute("SELECT COALESCE(SUM(quantidade*valor_unitario),0) FROM pedidos").fetchone()[0]
    return {"pedidos":pedidos,"produtos":produtos,"valor_pedidos":round(valor,2)}

def remove(db_path, action, data):
    # Exclusão simples e estritamente limitada a um identificador explícito.
    table, key = {"excluir_pedido":("pedidos","pedido_id"),"excluir_produto":("estoque","sku")}[action]
    ident=data[key]
    with sqlite3.connect(db_path) as db:
        cursor=db.execute(f"DELETE FROM {table} WHERE {key}=?", (ident,))
    if cursor.rowcount!=1:
        raise ValueError("Registro não encontrado; nada foi excluído.")
    return f"{action.replace('_',' ').capitalize()}: {ident} (1 registro)."
