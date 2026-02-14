# Sistema de Chamada da Crisma 🕊️

Este é um sistema web desenvolvido para facilitar o controle de presença dos crismandos em encontros de catequese. O projeto foi construído utilizando **Python** com o framework **Flask** e banco de dados **SQLite**.

---

## 🚀 Tecnologias Utilizadas

Para este projeto, utilizamos as seguintes ferramentas:

| Tecnologia | Função no Projeto |
| :--- | :--- |
| **Python** | A linguagem de programação principal (o "cérebro" do sistema). |
| **Flask** | Um "framework" que ajuda a criar sites com Python de forma rápida. |
| **SQLite** | Um banco de dados leve que guarda as informações em um arquivo local. |
| **Jinja2** | Motor de templates que permite misturar lógica Python dentro do HTML. |
| **HTML/CSS** | Responsáveis pela estrutura e aparência das páginas no navegador. |
| **JavaScript** | Adiciona interatividade e dinamismo às páginas web, como validações de formulário e manipulação de elementos na tela. |

---

## 🛠️ Como Funciona a Estrutura do Projeto

Aqui está uma explicação do que cada arquivo faz:

1.  **`app.py`**: É o arquivo principal. Ele contém as **Rotas**, que são os caminhos que o usuário acessa (ex: `/login`, `/homepage`). Ele recebe os dados do navegador, conversa com o banco de dados e decide qual página mostrar.
2.  **`create_db.py`**: Um script auxiliar. Você o executa apenas uma vez (ou quando precisar resetar) para criar as tabelas do banco de dados (`users`, `turmas`, `crismandos`, etc.).
3.  **`homepage.html`**: Um exemplo de arquivo de "Template". Ele define como a página inicial do usuário logado deve aparecer.
4.  **`data/dataBase.db`**: Onde todos os seus dados ficam salvos de verdade.
5.  **`.env`**: Um arquivo (geralmente escondido) que guarda senhas e configurações sensíveis, como a `MASTER_PASSWORD`.

---

## ⚙️ Como Instalar e Rodar

Se você estiver baixando este projeto pela primeira vez, siga estes passos:

1.  **Instale as dependências:**
    No terminal, rode o comando para instalar o Flask e as outras bibliotecas necessárias:
    ```bash
    pip install flask python-dotenv
    ```

2.  **Configure o ambiente:**
    Crie um arquivo chamado `.env` na raiz do projeto e adicione:
    ```env
    ADMIN_PASSWORD=sua_senha_admin
    MASTER_PASSWORD=sua_senha_mestre
    ```

3.  **Prepare o Banco de Dados:**
    Rode o script de criação das tabelas:
    ```bash
    python create_db.py
    ```

4.  **Inicie o Sistema:**
    Agora, basta rodar o servidor:
    ```bash
    python app.py
    ```
    O sistema estará disponível em `http://127.0.0.1:5000`.

---

## 🛡️ Segurança e Acesso

*   **Admin:** Tem acesso total, pode criar turmas e gerenciar crismandos.
*   **Catequistas:** Podem fazer login e registrar a presença nas turmas.
*   **Senha Mestre:** Utilizada para permitir que novos usuários se cadastrem no sistema, garantindo que apenas pessoas autorizadas criem contas.

---

## 📝 Próximos Passos Sugeridos
*   Melhorar o design das tabelas de chamada.
*   Adicionar relatórios de faltas por crismando.
*   Implementar a exportação da lista de chamada para PDF ou Excel.

---
*Desenvolvido com foco no aprendizado e na organização pastoral.*
