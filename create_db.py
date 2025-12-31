import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv
#teste
# =========================
# LOCALIZAÇÃO DO PROJETO
# =========================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "dataBase.db"

# =========================
# GARANTIR ESTRUTURA
# =========================

if not ENV_PATH.exists():
    raise RuntimeError(f".env não encontrado em {ENV_PATH}")

DATA_DIR.mkdir(exist_ok=True)

# =========================
# CARREGAR VARIÁVEIS DE AMBIENTE
# =========================

load_dotenv(ENV_PATH, override=True)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD")

if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD não encontrada no .env")

if not MASTER_PASSWORD:
    raise RuntimeError("MASTER_PASSWORD não encontrada no .env")

# =========================
# CRIAÇÃO DO BANCO
# =========================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# =========================
# TABELAS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS turmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turma_name TEXT NOT NULL UNIQUE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS crismandos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    turma_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (turma_id) REFERENCES turmas(id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tema TEXT NOT NULL,
    meeting_date TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crismando_id INTEGER NOT NULL,
    meeting_id INTEGER NOT NULL,
    status INTEGER NOT NULL CHECK (status IN (0, 1, 2)),
    FOREIGN KEY (crismando_id) REFERENCES crismandos(id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);
""")

# =========================
# USUÁRIO ADMIN (UPSERT)
# =========================

cursor.execute("""
INSERT INTO users (username, password, is_admin)
VALUES (?, ?, 1)
ON CONFLICT(username) DO UPDATE SET
password = excluded.password,
is_admin = 1
""", ("admin", ADMIN_PASSWORD))

conn.commit()
conn.close()