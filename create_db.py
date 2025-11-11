import sqlite3
import os

# Caminho do banco de dados dentro da pasta "data"
db_path = os.path.join("src", "data", "database.db")
#cria conexão com banco de dados, caso ele nao exista será criado
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Criar tabela de usuários (sem email)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
""")
conn.commit()
conn.close()