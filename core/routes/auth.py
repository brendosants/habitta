from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from core.extensions import bcrypt, mail
from core.utils.db_connection import get_db_connection
from core.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/tela/login", methods=["GET", "POST"])
def tela_login():
    if request.method == "POST":
        cpf = request.form.get("cpf", "").replace(".", "").replace("-", "")
        senha = request.form.get("senha", "")
        lembrar = True if request.form.get("lembrar") else False

        # Validação básica dos campos
        if not cpf or not senha:
            flash("CPF e senha são obrigatórios", "danger")
            return redirect(url_for("tela_login"))

        if len(cpf) != 11 or not cpf.isdigit():
            flash("CPF inválido. Deve conter 11 dígitos.", "danger")
            return redirect(url_for("tela_login"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Busca usuário por CPF
            cursor.execute(
                """
                SELECT id, nome, email, cpf, senha, nivel, avatar 
                FROM usuarios 
                WHERE cpf = %s
            """,
                (cpf,),
            )
            user_data = cursor.fetchone()

            if user_data and bcrypt.check_password_hash(user_data["senha"], senha):
                user = User(
                    id=user_data["id"],
                    nome=user_data["nome"],
                    email=user_data["email"],
                    cpf=user_data["cpf"],  # Adicione esta linha
                    nivel=user_data["nivel"],
                    avatar=user_data["avatar"],  # Adicionando o avatar
                )

                login_user(user, remember=lembrar)
                flash("Login realizado com sucesso!", "success")

                # Redireciona para página inicial ou URL armazenada
                next_page = request.args.get("next")
                return redirect(next_page or url_for("main.index"))
            else:
                flash("CPF ou senha incorretos", "danger")
        except Exception as e:
            flash("Erro ao processar login: " + str(e), "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("pages/auth/login.html")

@auth_bp.route('/tela/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            nome = request.form.get('nome', '').strip()
            sobrenome = request.form.get('sobrenome', '').strip()
            email = request.form.get('email', '').strip().lower()
            cpf = ''.join(filter(str.isdigit, request.form.get('cpf', '')))
            senha = request.form.get('senha', '').strip()
            confirmar_senha = request.form.get('confirmar_senha', '').strip()

            # Validações
            if len(cpf) != 11:
                flash('CPF deve conter 11 dígitos', 'danger')
                return redirect(url_for('auth.register'))

            if senha != confirmar_senha:
                flash('As senhas não coincidem', 'danger')
                return redirect(url_for('auth.register'))

            if len(senha) < 6:
                flash('Senha deve ter pelo menos 6 caracteres', 'danger')
                return redirect(url_for('auth.register'))

            conn = get_db_connection()
            cursor = conn.cursor()

            # Verificar se CPF ou email já existem (CORREÇÃO APLICADA AQUI)
            cursor.execute(
                "SELECT id FROM usuarios WHERE cpf = %s OR email = %s",
                (cpf, email)
            )
            
            if cursor.fetchone():
                flash('CPF ou email já cadastrados', 'danger')
                return redirect(url_for('auth.register'))

            # Criar hash da senha
            senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

            # Inserir novo usuário
            cursor.execute(
                """
                INSERT INTO usuarios 
                (nome, email, cpf, senha, nivel) 
                VALUES (%s, %s, %s, %s, 'comum')
                """,
                (f"{nome} {sobrenome}".strip(), email, cpf, senha_hash)
            )
            conn.commit()
            
            flash('Registro realizado com sucesso! Faça login', 'success')
            return redirect(url_for('auth.tela_login'))

        except Exception as e:
            print(f'Erro no registro: {str(e)}')
            flash('Erro durante o registro', 'danger')
            return redirect(url_for('auth.register'))
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return render_template('pages/auth/register.html')

@auth_bp.route("/recuperar-senha", methods=["GET", "POST"])
def recuperar_senha():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Verificar se o email existe
            cursor.execute("SELECT id, nome FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()

            if not usuario:
                flash("E-mail não encontrado em nosso sistema", "warning")
                return redirect(url_for("recuperar_senha"))

            # Gerar token de recuperação (simplificado)
            import secrets
            import datetime

            token = secrets.token_urlsafe(32)
            expiracao = datetime.datetime.now() + datetime.timedelta(hours=1)

            # Armazenar token no banco (você precisará criar esta tabela)
            cursor.execute(
                """
                INSERT INTO tokens_recuperacao 
                (usuario_id, token, expiracao) 
                VALUES (%s, %s, %s)
            """,
                (usuario["id"], token, expiracao),
            )
            conn.commit()

            # Enviar e-mail (exemplo simplificado)
            msg = Message("Redefinição de Senha - Habitta", recipients=[email])
            msg.body = f"""
            Olá {usuario['nome']},
            
            Para redefinir sua senha, clique no link abaixo:
            
            {url_for('redefinir_senha', token=token, _external=True)}
            
            Este link expira em 1 hora.
            
            Caso não tenha solicitado esta redefinição, ignore este e-mail.
            """

            mail.send(msg)
            flash("Um e-mail com instruções foi enviado!", "success")

        except Exception as e:
            print(f"Erro ao processar recuperação: {str(e)}")
            flash("Erro ao processar sua solicitação", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("pages/auth/forgot-password.html")

@auth_bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    # Implementação da lógica para redefinir a senha
    # Verificar token válido e permitir nova senha
    pass

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('main.index'))