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
# DEFAULT 0 é para sempre que um novo usuario for criado ele receber 0, já que só o admin recebe 1
# Inserir usuário admin apenas se ainda não existir

cursor.execute("""
INSERT OR IGNORE INTO users (username, password, is_admin)
VALUES ('admin', 'sfcrisma_admin', 1);
""")

conn.commit()
conn.close()
