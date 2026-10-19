import sqlite3
from flask import current_app, g

PENDENTE = "PENDENTE"
EM_ANDAMENTO = "EM_ANDAMENTO"
CONCLUIDA = "CONCLUIDA"
STATUS_VALIDOS = (PENDENTE, EM_ANDAMENTO, CONCLUIDA)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pwd_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    creation_date TEXT NOT NULL,
    deadline_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE'
        CHECK (status IN ('PENDENTE', 'EM_ANDAMENTO', 'CONCLUIDA')),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    get_db().executescript(SCHEMA)
    get_db().commit()
