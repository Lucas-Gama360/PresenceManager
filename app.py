import sqlite3
from flask import Flask, render_template
import os
def get_conn(): 
    conn = sqlite3.connect("data/dataBase.db")
    conn.row_factory = sqlite3.Row
    return conn

# Define que os templates estão na pasta "pages"
app = Flask(__name__, template_folder="src/pages")

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
