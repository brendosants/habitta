# app.py (versão limpa)
from flask import Flask
from core.extensions import mail, bcrypt, login_manager
from core.models import User  # Movemos a classe User para models.py

from core.utils.db_connection import get_db_connection
from core.utils.decorators import nivel_requerido

# Python Standard Library
import os
import csv
from functools import wraps
from io import StringIO, BytesIO
import traceback

# Third-party Libraries
import mysql.connector
import openpyxl
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt, generate_password_hash
from flask_login import (
    LoginManager,
    UserMixin,
)

# Flask Core
from flask import Flask

# 1. Primeiro cria a instância do Flask
app = Flask(__name__)

# 2. Configurações básicas
app.secret_key = os.urandom(24)  # Ou uma chave fixa em produção


# Importe TODOS os blueprints uma única vez
from core.routes.auth import auth_bp
from core.routes.clientes import clientes_bp
from core.routes.password import password_bp
from core.routes.estabelecimentos import estabelecimentos_bp
from core.routes.recomendacoes import recomendacoes_bp
from core.routes.main import main_bp

# Registre TODOS os blueprints uma única vez
app.register_blueprint(auth_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(password_bp)
app.register_blueprint(estabelecimentos_bp)
app.register_blueprint(recomendacoes_bp)
app.register_blueprint(main_bp)


# Configuração do Flask-Mail (adicione antes de criar o app)

app.config["MAIL_SERVER"] = "smtp.seuprovedor.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "seu@email.com"
app.config["MAIL_PASSWORD"] = "suasenha"
app.config["MAIL_DEFAULT_SENDER"] = "seu@email.com"

mail = Mail(app)

# Configurações
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth.tela_login"

# Modelo de Usuário
class User(UserMixin):
    def __init__(self, id, nome, email, cpf, nivel, avatar=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.cpf = cpf
        self.nivel = nivel
        self.avatar = avatar


# Carregador de usuário
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, nome, email, cpf, nivel FROM usuarios WHERE id = %s", (user_id,)
    )
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_data:
        return User(
            id=user_data["id"],
            nome=user_data["nome"],
            email=user_data["email"],
            cpf=user_data["cpf"],
            nivel=user_data["nivel"],
        )
    return None


@app.route('/debug-routes')
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.endpoint}: {rule.methods} → {rule.rule}")
    return '<pre>' + '\n'.join(routes) + '</pre>'

from core import create_app
from core.utils.logging import configure_logging

app = create_app()
configure_logging(app)  # ← Passe o app como argumento

if __name__ == '__main__':
    app.run(debug=True)