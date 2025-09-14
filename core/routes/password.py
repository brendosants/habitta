from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_mail import Message
from core.extensions import mail
from core.utils.db_connection import get_db_connection
import secrets
import datetime

password_bp = Blueprint('password', __name__)

@password_bp.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT id, nome FROM usuarios WHERE email = %s", 
                (email,))
            usuario = cursor.fetchone()

            if not usuario:
                flash('E-mail não encontrado em nosso sistema', 'warning')
                return redirect(url_for('password.recuperar_senha'))

            token = secrets.token_urlsafe(32)
            expiracao = datetime.datetime.now() + datetime.timedelta(hours=1)

            cursor.execute(
                """
                INSERT INTO tokens_recuperacao 
                (usuario_id, token, expiracao) 
                VALUES (%s, %s, %s)
                """,
                (usuario['id'], token, expiracao)
            )
            conn.commit()

            msg = Message('Redefinição de Senha', recipients=[email])
            msg.body = f"""
            Olá {usuario['nome']},
            
            Para redefinir sua senha, clique no link:
            {url_for('password.redefinir_senha', token=token, _external=True)}
            
            Link expira em 1 hora.
            """
            mail.send(msg)
            
            flash('Um e-mail com instruções foi enviado!', 'success')

        except Exception as e:
            print(f'Erro ao processar recuperação: {str(e)}')
            flash('Erro ao processar sua solicitação', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('auth/forgot-password.html')

@password_bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    # Implementação da redefinição de senha
    pass