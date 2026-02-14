import sqlite3
from flask import Flask, render_template, redirect, url_for, request, session
import os
import random
import secrets #pra poder gerar secret key aleatoria, segura(módulo nativo do python)
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# =========================
# LOCALIZAÇÃO DO PROJETO
# =========================
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
DB_PATH = BASE_DIR / "data" / "dataBase.db"

# carrega o .env EXPLICITAMENTE (mesmo padrão do create_db.py)
# Isso permite usar configurações como SECRET_KEY, DATABASE_URL, etc. sem precisar definir manualmente no terminal
load_dotenv(ENV_PATH, override=True)

# =========================
# CONEXÃO COM O BANCO 
# =========================
def get_conn(): 
    conn = sqlite3.connect("data/dataBase.db")
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# APP
# =========================

app = Flask(__name__)
#define senha mestre
# puxa do arquivo de enviroments
MASTER_PASSWORD = os.environ.get('MASTER_PASSWORD')

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
    # aqui eu estarei fazendo algumas interações com o db para o usuario poder carregar varias coisas sem precisar de url independente
    with get_conn() as conn:
        cur = conn.cursor()
        # Selecionamos encontros onde a data de criação é maior ou igual a "agora menos 1 dia"
        cur.execute("""
            SELECT id, tema, meeting_date 
            FROM meetings 
            WHERE created_at >= datetime('now', '-1 day', 'localtime')
            ORDER BY created_at DESC
        """)
        encontros = cur.fetchall()
        
        #Busco as turmas para o catequista escolher
        cur.execute("SELECT id, turma_name FROM turmas ORDER BY turma_name")
        turmas = cur.fetchall()
        conn.commit()
    return render_template('homepage.html', encontros=encontros, turmas=turmas)
    
@app.get('/configpage')
def config_page():
    """Página de configurações(admin)"""
    if 'admin' not in session :
        return render_template('index.html')
    else:
        return render_template('configpage.html')
#====================================
# ROTA NOVOS USUÁRIOSe
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

        # Busca todas os crismandos e ordena por nome
        cur.execute("SELECT id, name, turma_id FROM crismandos ORDER BY name")
        crismandos = cur.fetchall()
    
    # 3. Renderiza o Template
    # passa pro jinja a variavel turmas recebendo tudo que tem na tabela de turmas
    return render_template('turmas.html', turmas=turmas, msgturmas=msg, crismandos = crismandos)

@app.post('/deleteturma/<int:turma_id>/<nome>')
def delete_turma(turma_id , nome):
    if 'admin' not in session :
        return render_template('index.html')
    with get_conn() as conn:
        cur = conn.cursor()
                
        # 2. Excluir a turma
        cur.execute("DELETE FROM turmas WHERE id = ?", (turma_id,))
        conn.commit()

        # 2. Excluir os crismandos da turmas
        cur.execute("DELETE FROM crismandos WHERE turma_id = ?", (turma_id,))
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
        return redirect(url_for('list_turmas',msg=f'Erro inesperado: {str(e)}'))
    
#====================================
# ROTA VISUALIZAÇÃO DE TURMA USUÁRIOS
#==================================== 
@app.get("/viewturmas")
def view_turmas():
    if 'loged_user' not in session :
        return render_template('index.html')
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, turma_name FROM turmas ORDER BY turma_name")
        turmas = cur.fetchall()
        cur.execute("SELECT id, name, turma_id FROM crismandos ORDER BY name")
        crismandos = cur.fetchall()
    
    return render_template('viewturmas.html', turmas=turmas, crismandos = crismandos)
 
#====================================
# ROTAS EDIÇÃO DE CRISMANDOS
#====================================       
@app.get("/listcrismandos")
def list_crismandos():
    # puxa as msg das outras funções se eu tiver mandando, como na de deletar
    msg = request.args.get('msg')
    if not 'admin' in session:
        return render_template('index.html')
    else:
        with get_conn() as conn:
            cur = conn.cursor()
            # Busca todas as turmas e ordena por nome
            cur.execute("SELECT id, turma_name FROM turmas ORDER BY turma_name")
            turmas = cur.fetchall()
            # Busca todas os crismandos e ordena por nome
            cur.execute("SELECT id, name, turma_id FROM crismandos ORDER BY name")
            crismandos = cur.fetchall()
            return render_template('crismandos.html', turmas = turmas, msgcrismandos =msg, crismandos = crismandos)
        
@app.post("/addcrismandos/")
def add_crismandos():
    if not 'admin' in session:
        return render_template('index.html')
    
    namecrismando = request.form.get('add', '').strip() #strip retira o espaço do input
    turma_id = request.form.get("turma_id")
    if not namecrismando:
        return redirect(url_for('list_crismandos', msg='Erro: O nome do crismando não pode ser vazio.'))
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO crismandos (name, turma_id) VALUES (?, ?)", (namecrismando, turma_id))
            nome = cur.fetchall()
            conn.commit()
        return redirect(url_for('list_crismandos', msg='Crismando adicionado com sucesso!'))
    # violação do UNIQUE, ou seja, o crismando já está cadastrado
    except sqlite3.IntegrityError:
        return redirect(url_for('list_crismandos', msg=f'Erro: O"{namecrismando}" já está cadastrado.'))

@app.post("/deletecrismandos/<int:crismando_id>")
def delete_crismandos(crismando_id):
    if not 'admin' in session:
        return render_template('index.html')
    else:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM crismandos WHERE id = ?", (crismando_id,))
            cur.execute("DELETE FROM attendance WHERE crismando_id = ?", (crismando_id,))
            conn.commit()
            
        return redirect(url_for('list_crismandos', msg='Crismando retirado com sucesso!')) 

@app.post("/switchturma")
def switch_turma():
    crismando_id = int(request.form.get('crismando_id'))
    nova_turma = int(request.form.get('switch-turma'))
    if not 'admin' in session:
        return render_template('index.html')
    else:
        with get_conn() as conn:
            cur = conn.cursor()
            # A cláusula SET é usada para especificar quais colunas devem ser modificadas e qual será o novo valor para essas colunas.
            # A cláusula WHERE é usada para filtrar os registros. Ela define a condição que deve ser verdadeira para que um registro seja afetado pelo comando UPDATE.
            cur.execute("UPDATE crismandos SET turma_id = ? WHERE id = ?", (nova_turma, crismando_id))

            conn.commit()
        return redirect(url_for('list_crismandos', msg='Troca de turma efetuada com sucesso!')) 

@app.post('/randomcrismandos')
def random_crismandos():
    if not 'admin' in session:
        return render_template('index.html')
    else: 
        with get_conn() as conn:
            cur = conn.cursor()

            #Buscar crismandos como LISTA DE INTS
            cur.execute("SELECT id FROM crismandos")
            crismandos = [row[0] for row in cur.fetchall()]

            #Buscar turmas como LISTA DE INTS
            cur.execute("SELECT id FROM turmas")
            turmas = [row[0] for row in cur.fetchall()]  # row[0] pega a coluna da linha salva no fetchal, usamos assim para transformar em um array simples, não tuplas

            if not turmas:
                return redirect(url_for('list_crismandos', msg="Erro: Nenhuma turma cadastrada."))

            if not crismandos:
                return redirect(url_for('list_crismandos', msg="Erro: Nenhum crismando para redistribuir."))

            # Embaralhar de forma aleatória
            random.shuffle(crismandos)
            random.shuffle(turmas)

            # Atribuir turmas em ordem cíclica
            atualizacoes = []
            for i, crismando_id in enumerate(crismandos):
                turma_id = turmas[i % len(turmas)]
                atualizacoes.append((turma_id, crismando_id))  # ← agora são inteiros!

            #Executar em lote — sem erros!
            cur.executemany(
                "UPDATE crismandos SET turma_id = ? WHERE id = ?",
                atualizacoes
            )

            
            conn.commit()
            return redirect(url_for('list_crismandos', msg= "Turmas Redistribuidas com sucesso!"))

        #  REDISTRIBUIÇÃO EQUILIBRADA (round-robin aleatório)
        # 
        # Objetivo: Distribuir N crismandos em T turmas, com diferença máxima de 1 crismando entre turmas.
        # Estratégia:
        #   1. Embaralhamos crismandos e turmas → justiça (ninguém sempre na turma 1).
        #   2. Atribuímos em ordem cíclica usando: `turma_id = turmas[i % len(turmas)]`
        #      - Ex: 10 crismandos + 3 turmas → índices: 0,1,2,0,1,2,0,1,2,0 → turmas: [A,B,C,A,B,C,A,B,C,A]
        #      - Resultado: A=4, B=3, C=3 → equilíbrio perfeito.
        #   3. Armazenamos cada atualização como (nova_turma_id, crismando_id),
        #      na mesma ordem dos placeholders `?` no SQL: "SET turma_id = ? WHERE id = ?"
        

#========================================
# ROTAS GERENCIAMENTO DE ENCONTROS(ADMIN)
#========================================
@app.get("/listmeettings")
def list_meetings():

    if not 'admin' in session:
        return render_template('index.html')
    else:
        msg = request.args.get('msg')
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, tema, meeting_date FROM meetings ORDER BY created_at")
            encontros = cur.fetchall()

        return render_template('managemeetings.html', encontros=encontros, msg=msg)
    
@app.post("/createmeeting")
def create_meetings():
    if not 'admin' in session:
        return render_template('index.html')
    else:
        tema = request.form.get('tema', '').strip()
        data = request.form.get('meeting-date', '').strip()

        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO meetings (tema, meeting_date) VALUES (?,?)", (tema, data))
            conn.commit()
        return redirect(url_for('list_meetings', msg='Encontro registrado com sucesso!'))
    
@app.post("/deletemeeting")
def delete_meeting():
    if not 'admin' in session:
        return render_template('index.html')
    else:
        meetingid = request.form.get('meeting-id')
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM meetings WHERE id = ?", (meetingid,))
            conn.commit()
        return redirect(url_for('list_meetings', msg = 'Encontro deletado com sucesso!'))
    
#========================================
# ROTAS REALIZAÇÃO E EDIÇÃO DE CHAMADAS
#========================================
@app.post("/requirementsattendance")
def requirements_attendance():
    if 'loged_user' not in session:
        return render_template("index.html")

    encontro_id = request.form.get('openmeetings')
    turma_id = request.form.get('turmaattendance')

    # Salva os IDs no session ou redireciona com eles
    return redirect(url_for('list_attendance', encontro_id=encontro_id, turma_id=turma_id))

@app.get("/listattendance")
def list_attendance():
    encontro_id = request.args.get('encontro_id')
    turma_id = request.args.get('turma_id')

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM meetings WHERE id = ?", (encontro_id,))
        encontroselect = cur.fetchone()

        cur.execute("SELECT * FROM turmas WHERE id = ?", (turma_id,))
        turmaselect = cur.fetchone()

        cur.execute("SELECT * FROM crismandos WHERE turma_id = ?", (turma_id,))
        crismandos = cur.fetchall()

    return render_template('attendance.html', encontroselect=encontroselect, turmaselect=turmaselect, crismandos=crismandos)

@app.post("/saveattendance")
def save_attendance():
    if 'loged_user' not in session:
        return render_template("index.html")
    # 1. O seu HTML tem: <input type="hidden" name="meeting_id" value="{{ encontroselect.id }}">
    # Então aqui buscamos pelo nome 'meeting_id'
    meeting_id = request.form.get('meeting_id')
    
    with get_conn() as conn:
        cur = conn.cursor()
        
        # 2. Vamos varrer todos os campos que o formulário enviou
        for key, value in request.form.items():
            
            # 3. No seu HTML, o select tem: name="status_{{aluno.id}}"
            # Se o aluno tem ID 7, o nome do campo chega como "status_7"
            if key.startswith('status_'):
                
                # 4. Tiramos o "status_" para sobrar só o número do ID do aluno
                crismando_id = key.replace('status_', '')
                
                # 5. O valor (value) será 0 (Presente), 1 (Falta) ou 2 (Justificado)
                status = int(value)
                
                # 6. AGORA A INTERAÇÃO COM O BANCO:
                # Inserimos na tabela 'attendance' que você criou no create_db.py
                cur.execute("""
                    INSERT OR REPLACE INTO attendance (crismando_id, meeting_id, status)
                    VALUES (?, ?, ?)
                """, (crismando_id, meeting_id, status))
        
        conn.commit()
    
    return redirect(url_for('home_page'))

@app.post("/saveattendanceedit")
def save_attendance_edit():
    if 'loged_user' not in session:
        return render_template("index.html")
    # 1. O seu HTML tem: <input type="hidden" name="meeting_id" value="{{ encontroselect.id }}">
    # Então aqui buscamos pelo nome 'meeting_id'
    meeting_id = request.form.get('meeting_id')
    
    with get_conn() as conn:
        cur = conn.cursor()
        
        # 2. Vamos varrer todos os campos que o formulário enviou
        for key, value in request.form.items():
            
            # 3. No seu HTML, o select tem: name="status_{{aluno.id}}"
            # Se o aluno tem ID 7, o nome do campo chega como "status_7"
            if key.startswith('status_'):
                
                # 4. Tiramos o "status_" para sobrar só o número do ID do aluno
                crismando_id = key.replace('status_', '')
                
                # 5. O valor (value) será 0 (Presente), 1 (Falta) ou 2 (Justificado)
                status = int(value)
                
                # 6. AGORA A INTERAÇÃO COM O BANCO:
                # Inserimos na tabela 'attendance' que você criou no create_db.py
                cur.execute("""
                    INSERT OR REPLACE INTO attendance (crismando_id, meeting_id, status)
                    VALUES (?, ?, ?)
                """, (crismando_id, meeting_id, status))
        
        conn.commit()
    
    return redirect(url_for('edit_attendance'))

@app.get('/editattendance')
def edit_attendance():
    """Página com o grid de encontros e a tabela de resumo dos últimos 10 encontros"""
    if 'loged_user' not in session:
        return render_template('index.html')
    
    with get_conn() as conn:
        cur = conn.cursor()
        
        # 1. Buscar todos os encontros para o Grid (do mais novo para o mais antigo)
        cur.execute("SELECT id, tema, meeting_date FROM meetings ORDER BY meeting_date DESC")
        encontros = cur.fetchall()
        
        # 2. Buscar todas as turmas para o Modal de seleção
        cur.execute("SELECT id, turma_name FROM turmas ORDER BY turma_name")
        turmas = cur.fetchall()
        
        # 3. Buscar os últimos 10 encontros para a Tabela de Resumo
        cur.execute("SELECT id, meeting_date FROM meetings ORDER BY meeting_date DESC LIMIT 10")
        encontros_tabela = cur.fetchall()
        encontros_tabela = encontros_tabela[::-1] # Inverte para o mais novo ficar na direita
        
        # 4. Buscar todos os crismandos para a primeira coluna da tabela
        cur.execute("SELECT id, name FROM crismandos ORDER BY name")
        crismandos = cur.fetchall()
        
        # 5. Criar um mapa de presenças (Dicionário)
        # Isso evita fazer centenas de consultas ao banco dentro do HTML
        presencas_map = {}
        if encontros_tabela:
            meeting_ids = [str(e['id']) for e in encontros_tabela]
            placeholders = ','.join(['?'] * len(meeting_ids))
            query = f"SELECT crismando_id, meeting_id, status FROM attendance WHERE meeting_id IN ({placeholders})"
            cur.execute(query, [int(i) for i in meeting_ids])
            presencas = cur.fetchall()
            
            for p in presencas:
                # Criamos uma chave única: "IDdoAluno_IDdoEncontro"
                key = f"{p['crismando_id']}_{p['meeting_id']}"
                presencas_map[key] = p['status']

    return render_template('editattendance.html', 
                           encontros=encontros, 
                           turmas=turmas, 
                           encontros_tabela=encontros_tabela, 
                           crismandos=crismandos, 
                           presencas_map=presencas_map)

@app.get('/editattendanceview')
def edit_attendance_view():
    """Página que abre a lista de alunos de uma turma específica para editar"""
    if 'loged_user' not in session:
        return render_template('index.html')
    
    encontro_id = request.args.get('encontro_id')
    turma_id = request.args.get('turma_id')
    
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, tema, meeting_date FROM meetings WHERE id = ?", (encontro_id,))
        encontro = cur.fetchone()
        
        cur.execute("SELECT id, turma_name FROM turmas WHERE id = ?", (turma_id,))
        turma = cur.fetchone()
        
        # O LEFT JOIN busca o aluno mesmo que ele ainda não tenha presença marcada
        cur.execute("""
            SELECT c.id, c.name, a.status 
            FROM crismandos c
            LEFT JOIN attendance a ON c.id = a.crismando_id AND a.meeting_id = ?
            WHERE c.turma_id = ?
            ORDER BY c.name
        """, (encontro_id, turma_id))
        lista_presenca = cur.fetchall()

    return render_template('edit_attendance_view.html', 
                           encontro=encontro, 
                           turma=turma, 
                           lista_presenca=lista_presenca)

#====================================
# ROTA FREQUÊNCIA (ÚLTIMOS 3 ENCONTROS)
#====================================
@app.get("/frequency")
def frequency_report():
    """Calcula a frequência dos crismandos de forma ultra simples"""
    # 1. Segurança: Só entra se estiver logado
    if 'loged_user' not in session:
        return render_template('index.html')
    
    # 2. Conecta ao banco de dados
    conn = get_conn()
    cur = conn.cursor()
    
    # 3. Busca os IDs dos 3 encontros mais recentes pela data
    cur.execute("SELECT id FROM meetings ORDER BY meeting_date DESC LIMIT 5")
    encontros = cur.fetchall()
    lista_ids = [e['id'] for e in encontros]
    total_encontros = len(lista_ids)
    
    # 4. Busca todos os crismandos (apenas o básico: id e nome)
    cur.execute("SELECT id, name FROM crismandos")
    todos_crismandos = cur.fetchall()
    
    relatorio = []
    
    # 5. Para cada aluno, vamos contar as presenças
    for aluno in todos_crismandos:
        presencas = 0
        for id_encontro in lista_ids:
            # Verifica na tabela 'attendance' se o aluno tem status 0 (presente)
            cur.execute("SELECT status FROM attendance WHERE crismando_id = ? AND meeting_id = ?", 
                        (aluno['id'], id_encontro))
            resultado = cur.fetchone()
            
            # Se encontrou o registro e o status for 0, soma 1 presença
            if resultado and resultado['status'] == 0:
                presencas += 1
        
        # 6. Calcula a porcentagem (Presenças divididas pelo Total de Encontros)
        if total_encontros > 0:
            porcentagem = (presencas / total_encontros) * 100
        else:
            porcentagem = 0
            
        # Adiciona os dados simplificados na lista que vai para o HTML
        relatorio.append({
            'nome': aluno['name'],
            'percentual': int(porcentagem) # int() remove as casas decimais
        })
    
    # 7. Fecha a conexão e envia os dados para a página
    conn.close()
    return render_template('frequency.html', report=relatorio)

#====================================
# ROTA RESET DB
#====================================
@app.post("/reset_database")
def reset_database():
    
    if not 'admin' in session:
        return render_template('index.html')
    
    passwordmaster = request.form.get('senhamestre', '').strip()
    if passwordmaster == MASTER_PASSWORD:
        with get_conn() as conn:
            cur = conn.cursor()
        
            # 2. Apagamos os dados das tabelas na ordem correta (por causa das chaves estrangeiras)
            # Primeiro as presenças, depois crismandos, depois turmas e encontros
            cur.execute("DELETE FROM attendance")
            cur.execute("DELETE FROM crismandos")
            cur.execute("DELETE FROM turmas")
            cur.execute("DELETE FROM meetings")
            cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('attendance', 'crismandos', 'turmas', 'meetings')")
        
            conn.commit()
    
        # 4. Redireciona de volta para a página de configurações com uma mensagem
        return redirect(url_for('config_page', msg="Banco de dados resetado com sucesso! (Usuários mantidos)"))
    else:
        return redirect(url_for('config_page', msg="Senha Mestre errada, o sistema não foi resetado.")) 

#====================================
# FUNÇÃO LOGOUT
#====================================
@app.post("/logout")
def logout_user():
    """Desloga o usuário"""
    session.clear()
    return render_template('index.html')


    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)