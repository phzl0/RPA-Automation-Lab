"""Métricas administrativas e log de alterações manuais do ERP local.

Os horários são persistidos em UTC; a interface os identifica como UTC.
O usuário exibido é uma origem funcional, não uma identidade autenticada.
"""
import sqlite3
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def initialize(db_path):
    with sqlite3.connect(db_path,timeout=15) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS activity_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            source TEXT NOT NULL,
            actor_label TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_activity_recent ON activity_log(id DESC)")

def record(db_path,action,entity_type,entity_id,detail="",source="manual",status="sucesso"):
    now=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    actor="ADM (manual)" if source=="manual" else "RPA (assistido)"
    with sqlite3.connect(db_path,timeout=15) as db:
        db.execute("""INSERT INTO activity_log
            (occurred_at,action,entity_type,entity_id,source,actor_label,status,detail)
            VALUES (?,?,?,?,?,?,?,?)""",
            (now,action,entity_type,str(entity_id),source,actor,status,str(detail)[:500]))

def recent(db_path,limit=30):
    with sqlite3.connect(db_path,timeout=15) as db:
        db.row_factory=sqlite3.Row
        events=[dict(r) for r in db.execute("""
        SELECT occurred_at,action,entity_type,entity_id,source,actor_label,status,detail
        FROM activity_log ORDER BY id DESC LIMIT ?""",(min(limit,100),))]
        # rpa_audit preceded activity_log; retain old RPA operations in the dashboard.
        legacy=[dict(r) for r in db.execute("""
        SELECT created_at AS occurred_at,action,
        CASE WHEN action LIKE '%pedido%' THEN 'pedido' ELSE 'produto' END AS entity_type,
        '' AS entity_id,'rpa' AS source,'RPA (assistido)' AS actor_label,status,
        COALESCE(detail,'') AS detail
        FROM rpa_audit ORDER BY id DESC LIMIT ?""",(min(limit,100),))]
    def enrich(item, origin):
        item["origin"] = origin
        try:
            parsed = datetime.strptime(item["occurred_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            item["occurred_local"] = parsed.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
        except (TypeError, ValueError):
            item["occurred_local"] = item["occurred_at"] or "—"
    for e in events: enrich(e, "manual")
    for e in legacy: enrich(e, "rpa")
    return sorted(events+legacy,key=lambda e:(e["occurred_at"] or ""),reverse=True)[:limit]

def metrics(db_path):
    with sqlite3.connect(db_path,timeout=15) as db:
        db.row_factory=sqlite3.Row
        def scalar(q): return db.execute(q).fetchone()[0]
        totals={
            "orders":scalar("SELECT COUNT(*) FROM pedidos"),
            "orders_value":round(scalar("SELECT COALESCE(SUM(quantidade*valor_unitario),0) FROM pedidos"),2),
            "products":scalar("SELECT COUNT(*) FROM estoque"),
            "low_stock":scalar("SELECT COUNT(*) FROM estoque WHERE quantidade<=5"),
            "pending":scalar("SELECT COUNT(*) FROM pedidos WHERE status='pendente'"),
            "completed":scalar("SELECT COUNT(*) FROM pedidos WHERE status='concluido'"),
            "conversations":scalar("SELECT COUNT(*) FROM chat_conversations"),
            "rpa_success":scalar("SELECT COUNT(*) FROM rpa_audit WHERE status='sucesso'"),
            "rpa_errors":scalar("SELECT COUNT(*) FROM rpa_audit WHERE status='erro'"),
            "manual_actions":scalar("SELECT COUNT(*) FROM activity_log WHERE status='sucesso'"),
        }
        recent_orders=[dict(r) for r in db.execute(
            "SELECT pedido_id,cliente,produto,quantidade,valor_unitario,status FROM pedidos ORDER BY rowid DESC LIMIT 6")]
        low_products=[dict(r) for r in db.execute(
            "SELECT sku,produto,quantidade FROM estoque ORDER BY quantidade ASC,sku ASC LIMIT 6")]
    return {"totals":totals,"orders":recent_orders,"products":low_products,"activity":recent(db_path,8)}
