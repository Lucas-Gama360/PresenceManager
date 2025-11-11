import sqlite3
from flask import Flask, render_template
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
@app.route("/")
def home():
    return render_template("index.html")

@app.get('/register')
def register_page():
    """Página de cadastro"""
    return render_template('CreateAccount.html')

@app.get('/login')
def login_page():
    """Página de Login"""
    return render_template('index.html')

c
if __name__ == "__main__":
    app.run(debug=True)
