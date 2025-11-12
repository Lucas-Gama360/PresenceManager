import sqlite3
from flask import Flask, render_template, redirect, url_for, request
import os

def get_conn(): 
    conn = sqlite3.connect("data/dataBase.db")
    conn.row_factory = sqlite3.Row
    return conn

# Define que os templates estão na pasta "pages"
app = Flask(__name__, 
            template_folder="src/pages",
            static_folder="src/static")


#====================================
# ROTAS PÁGINAS INICIAIS
#====================================
@app.route('/')
def index():
    return render_template("index.html")

@app.get('/register')
def register_page():
    """Página de cadastro"""
    return render_template('CreateAccount.html')

#====================================
# ROTA NOVOS USUÁRIOS
#====================================
@app.route('/register_user', methods=['POST'])
def register_user():
    """Cria uma nova conta de usuário"""
    username = request.form.get('nome', '').strip()
    password = request.form.get('senha', '').strip()
    try:
        # Adiciona novo usuário
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except:
        return redirect(url_for('register_page', msg='Usuário e/ou e-mail já cadastrados.'))
    finally:
        conn.close()

    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
