import sqlite3
from flask import Flask, render_template, redirect, url_for, request
import os

def get_conn(): 
    conn = sqlite3.connect("data/dataBase.db")
    conn.row_factory = sqlite3.Row
    return conn

# Define que os templates estão na pasta "pages"
app = Flask(__name__)


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

@app.get('/homepage')
def home_page():
    """Página de cadastro"""
    return render_template('homepage.html')

#====================================
# ROTA NOVOS USUÁRIOS
#====================================
@app.post('/register_user')
def register_user():
    """Cria uma nova conta de usuário"""
    username = request.form.get('nome', '').strip() #strip retira o espaço do input
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
#====================================
# ROTA LOGIN DE USUÁRIOS
#====================================
@app.post('/login')
def login_user():
    """Pega as informações dos inputs"""
    username = request.form.get('nome', '').strip()
    password = request.form.get('senha', '').strip()

    with get_conn() as conn:
        
        cur = conn.cursor()

        cur.execute("SELECT username, password FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()

        if user is None:
            return redirect(url_for('index', msg1='Usuário não encontrado'))
        
        return redirect(url_for('home_page'))
    

    







    
if __name__ == "__main__":
    app.run(debug=True)
