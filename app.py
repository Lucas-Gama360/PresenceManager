import sqlite3
from flask import Flask, render_template, redirect, url_for, request, session
import os
import random
import secrets #pra poder gerar secret key aleatoria, segura(módulo nativo do python)
from dotenv import load_dotenv
from pathlib import Path

# =========================
# CARREGAR .env CORRETAMENTE
# =========================
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

def get_conn(): 
    conn = sqlite3.connect(BASE_DIR / "data" / "dataBase.db")
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)

#define senha mestre
# puxa do arquivo de enviroments
MASTER_PASSWORD = os.environ.get('MASTER_PASSWORD')

if not MASTER_PASSWORD:
    raise RuntimeError("MASTER_PASSWORD não encontrada no .env")

#  gera aleatoriamente a secret key
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)


#====================================
# ROTAS PÁGINAS 
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
    """Página inicial"""
    if 'loged_user' not in session :
        return render_template("index.html")
    
    return render_template('homepage.html')

@app.get('/configpage')
def config_page():
    """Página de configurações(admin)"""
    if 'admin' not in session :
        return render_template('index.html')
    else:
        return render_template('configpage.html')


#====================================
# ROTA NOVOS USUÁRIOS
#====================================
@app.post('/register_user')
def register_user():
    """Cria uma nova conta de usuário"""
    username = request.form.get('nome', '').strip() #strip retira o espaço do input
    password = request.form.get('senha', '').strip()
    passwordmaster = request.form.get('senha-mestre', '').strip()

    if not username or not password:
        return redirect(url_for('register_page', msg='Erro: Nome de usuário e senha não podem ser vazios.'))
        
    if passwordmaster == MASTER_PASSWORD:
        try:
            # Adiciona novo usuário
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except:
            return redirect(url_for('register_page', msg='Usuário e/ou e-mail já cadastrados.'))
        finally:
            conn.close()
        return redirect(url_for('index'))
    else: #A senha mestre logicamente está incorreta
        return redirect(url_for(
            'register_page',
            msg='A senha mestre digitada está incorreta. Não foi possível criar a conta'
        ))


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

        cur.execute(
            "SELECT username, password, is_admin FROM users WHERE username = ? AND password = ?",
            (username, password)
        )

        # user é a variavel que salva em formato de dicionario de python para ser possivel salvar sessões
        user = cur.fetchone()

        if user is None:
            return redirect(url_for('index', msg1='Usuário não encontrado'))
        
        # Salva na sessão, e ai usando JINJA Eu configuro o html do home page pro admin
        # A sessão no Flask é um mecanismo que armazena dados temporários do usuário entre requisições
        session['loged_user'] = user['username']
        session['admin'] = user['is_admin'] 

        return redirect(url_for('home_page'))


#====================================
# FUNÇÃO LOGOUT
#====================================
@app.post("/logout")
def logout_user():
    """Desloga o usuário"""
    session.clear()
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
