"""Histórico compartilhado por chat web e CLI no banco SQLite do laboratório."""
import sqlite3
from uuid import uuid4

def init_chat(db_path):
    with sqlite3.connect(db_path, timeout=15) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS chat_conversations (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','model','system')),
            text TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(conversation_id) REFERENCES chat_conversations(id))""")
        db.execute("""CREATE TABLE IF NOT EXISTS rpa_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT, action TEXT NOT NULL,
            payload TEXT NOT NULL, status TEXT NOT NULL, detail TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def connect(db_path):
    db = sqlite3.connect(db_path, timeout=15)
    db.row_factory = sqlite3.Row
    return db

def new_conversation(db_path, title="Nova conversa"):
    ident = uuid4().hex
    with connect(db_path) as db:
        db.execute("INSERT INTO chat_conversations (id,title) VALUES (?,?)", (ident, title[:80]))
    return ident

def list_conversations(db_path):
    with connect(db_path) as db:
        return [dict(row) for row in db.execute("SELECT id,title,created_at,updated_at FROM chat_conversations ORDER BY updated_at DESC LIMIT 100")]

def get_messages(db_path, ident, limit=100):
    with connect(db_path) as db:
        exists = db.execute("SELECT id FROM chat_conversations WHERE id=?", (ident,)).fetchone()
        if not exists:
            raise ValueError("Conversa não encontrada.")
        rows = db.execute("SELECT role,text,created_at FROM (SELECT id,role,text,created_at FROM chat_messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?) ORDER BY id ASC", (ident, min(limit,200)))
        return [dict(row) for row in rows]

def save_message(db_path, ident, role, text):
    if role not in ("user","model","system"):
        raise ValueError("Papel inválido.")
    with connect(db_path) as db:
        count = db.execute("SELECT COUNT(*) FROM chat_messages WHERE conversation_id=?", (ident,)).fetchone()[0]
        if count == 0 and role == "user":
            db.execute("UPDATE chat_conversations SET title=? WHERE id=?", (text[:75], ident))
        updated = db.execute("UPDATE chat_conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (ident,))
        if updated.rowcount != 1:
            raise ValueError("Conversa não encontrada.")
        db.execute("INSERT INTO chat_messages(conversation_id,role,text) VALUES (?,?,?)", (ident, role, text[:10000]))

def delete_conversation(db_path, ident):
    with connect(db_path) as db:
        db.execute("DELETE FROM chat_messages WHERE conversation_id=?", (ident,))
        db.execute("DELETE FROM chat_conversations WHERE id=?", (ident,))

def audit(db_path, ident, action, payload, status, detail):
    import json
    with connect(db_path) as db:
        db.execute("INSERT INTO rpa_audit(conversation_id,action,payload,status,detail) VALUES (?,?,?,?,?)",
                   (ident, action, json.dumps(payload, ensure_ascii=False), status, str(detail)[:1000]))
