import sqlite3
from flask import Flask, render_template, redirect, url_for, request, session
import os

def get_conn(): 
    conn = sqlite3.connect("data/dataBase.db")
    conn.row_factory = sqlite3.Row
    return conn

# Define que os templates estão na pasta "pages"
app = Flask(__name__)
#define senha mestre
MASTER_PASSWORD =   "sfcrisma"
app.config['SECRET_KEY'] = 'ufw$hR!o&b|vtP%3' # Adicionar chave secreta para sessões


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
    """Página de cadastro"""
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
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except:
            return redirect(url_for('register_page', msg='Usuário e/ou e-mail já cadastrados.'))
        finally:
            conn.close()
        return redirect(url_for('index'))
    else: #A senha mestre logicamente está inocrreta
        return redirect(url_for('register_page', msg='A senha mestre digitada está incorreta. Não foi possível criar a conta'))
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

        cur.execute("SELECT username, password, is_admin FROM users WHERE username = ? AND password = ?", (username, password))
        # user é a variavel que salva em formato de dicionario de python para ser possivel salvar sessões
        user = cur.fetchone()
        if user is None:
            return redirect(url_for('index', msg1='Usuário não encontrado'))
        
        # Salva na sessão, e ai usando JINJA Eu configuro o html do home page pro admin
        # A sessão no Flask é um mecanismo que armazena dados temporários do usuário entre requisições, usando um cookie criptografado chamado session. Quando o usuário faz login, o Flask salva informações (como ID e nome)
        # eu posso utilizar os dados da sessão novamente se necessário
        # Aqui é configurado as sessões
        session['loged_user'] = user['username']
        session['admin'] = user['is_admin'] 

        return redirect(url_for('home_page'))
#====================================
# ROTAS TURMAS(ADMIN)
#====================================
@app.get('/listturmas')
def list_turmas():
    """Página de edição de turma(admin)"""
    if 'admin' not in session :
        return render_template('index.html')
    # puxa as msg das outras funções se eu tiver mandando, como na de deletar
    msg = request.args.get('msg')
    with get_conn() as conn:
        cur = conn.cursor()
        # Busca todas as turmas e ordena por nome
        cur.execute("SELECT id, turma_name FROM turmas ORDER BY turma_name")
        turmas = cur.fetchall()
    
    # 3. Renderiza o Template
    # passa pro jinja a variavel turmas recebendo tudo que tem na tabela de turmas
    return render_template('addturmas.html', turmas=turmas, msgturmas=msg)

@app.post('/deleteturma/<int:turma_id>/<nome>')
def delete_turma(turma_id , nome):
    if 'admin' not in session :
        return render_template('index.html')
    with get_conn() as conn:
        cur = conn.cursor()
            
        # 1. Verificar se há crismandos vinculados
        # cur.execute("SELECT COUNT(*) FROM crismandos WHERE turma_id = ?", (turma_id,))
        # if cur.fetchone()[0] > 0:
            # return redirect(url_for('list_turmas', msg='Erro: Não é possível excluir a turma. Existem crismandos vinculados a ela.'))
                
        # 2. Excluir a turma
        cur.execute("DELETE FROM turmas WHERE id = ?", (turma_id,))
        conn.commit()
            
        return redirect(url_for('list_turmas', msg=f'{nome} excluida com sucesso!'))

@app.post("/creaturma")
def create_turma():
    if 'admin' not in session:
        return redirect(url_for('index', msg='Acesso negado.'))

    # 1. Captura o nome da turma e remove espaços em branco do início e do fim
    turmaname = request.form.get('name', '').strip()

    # 2. Verifica se o nome da turma está vazio após o strip()
    if not turmaname:
        # Se estiver vazio, redireciona de volta com uma mensagem de erro
        return redirect(url_for('list_turmas', msg='Erro: O nome da turma não pode ser vazio.'))

    # Se o nome for válido, prossegue com a inserção no banco de dados
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO turmas (turma_name) VALUES (?)", (turmaname,))
            conn.commit()
            return redirect(url_for('list_turmas', msg=f'"{turmaname}" criada com sucesso!'))
    # Se cair aqui, o nome já existe (violação do UNIQUE)
    except sqlite3.IntegrityError:
        return redirect(url_for('list_turmas',msg=f'Erro: A turma "{turmaname}" já existe.'))
    # captura qualquer erro inesperado
    except Exception as e:
        return redirect(url_for('list_turmas',
                                msg=f'Erro inesperado: {str(e)}'))

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
