import sqlite3
import os

# Caminho do banco de dados dentro da pasta "data"
db_path = os.path.join("data", "dataBase.db")

# cria conexão com banco de dados, caso ele nao exista será criado
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Criar tabela de usuários com campo is_admin
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0 
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
CREATE TABLE IF NOT EXISTS turmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turma_name TEXT NOT NULL UNIQUE                            
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    turma_id INTEGER NOT NULL,
    FOREIGN KEY (turma_id) REFERENCES turmas(id)
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crismando_id INTEGER NOT NULL,
    meeting_id INTEGER NOT NULL,
    
    -- 0 = falta | 1 = presente | 2 = justificada
    status INTEGER NOT NULL CHECK (status IN (0, 1, 2)),
    
    FOREIGN KEY (crismando_id) REFERENCES crismandos(id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);
""")
# DEFAULT 0 é para sempre que um novo usuario for criado ele receber 0, já que só o admin recebe 1
# Inserir usuário admin apenas se ainda não existir

cursor.execute("""
INSERT OR IGNORE INTO users (username, password, is_admin)
VALUES ('admin', 'sfcrisma_admin', 1);
""")

conn.commit()
conn.close()
