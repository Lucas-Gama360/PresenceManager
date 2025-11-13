import sqlite3

# Caminho do seu banco
DB_PATH = "data/dataBase.db"  # altere para o nome correto, ex: "instance/users.db"

def limpar_tabela(users):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(f"DELETE FROM {users};")
        conn.commit()
        print(f"Tabela '{users}' limpa com sucesso!")
    except Exception as e:
        print("Erro ao limpar tabela:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    limpar_tabela("users")  # substitua pelo nome da tabela que deseja limpar
