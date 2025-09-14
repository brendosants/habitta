from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, login_user, current_user
from core.utils.db_connection import get_db_connection
from core.extensions import bcrypt
from core.models import User
from core.utils.file_handlers import save_avatar, validate_image
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)

@profile_bp.route("/atualizar-perfil", methods=["POST"])
@login_required
def atualizar_perfil():
    try:
        # Dados do formulário
        nome = request.form.get("nome")
        email = request.form.get("email")
        cpf = request.form.get("cpf", "").replace(".", "").replace("-", "")
        senha = request.form.get("senha")

        # Validações básicas
        if not nome or not email or not cpf:
            return jsonify({
                "success": False,
                "message": "Nome, CPF e e-mail são obrigatórios"
            }), 400

        if len(cpf) != 11 or not cpf.isdigit():
            return jsonify({
                "success": False,
                "message": "CPF inválido. Deve conter 11 dígitos."
            }), 400

        if senha and senha != request.form.get("confirmar_senha"):
            return jsonify({
                "success": False,
                "message": "As senhas não coincidem"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verifica se CPF já existe
        cursor.execute(
            "SELECT id FROM usuarios WHERE cpf = %s AND id != %s",
            (cpf, current_user.id)
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "message": "Este CPF já está cadastrado para outro usuário."
            }), 400

        # Processar avatar
        avatar_url = current_user.avatar
        if "avatar" in request.files:
            arquivo = request.files["avatar"]
            if arquivo.filename != "":
                avatar_url = save_avatar(arquivo, current_user)

        # Atualizar dados no banco
        update_fields = {
            "nome": nome,
            "email": email,
            "cpf": cpf,
            "avatar": avatar_url
        }

        if senha:
            update_fields["senha"] = bcrypt.generate_password_hash(senha).decode("utf-8")

        # Monta e executa a query
        set_clause = ", ".join([f"{field} = %s" for field in update_fields.keys()])
        query = f"UPDATE usuarios SET {set_clause} WHERE id = %s"
        cursor.execute(query, tuple(update_fields.values()) + (current_user.id,))
        conn.commit()

        # Recarrega os dados do usuário
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (current_user.id,))
        updated_user_data = cursor.fetchone()
        conn.close()

        if not updated_user_data:
            return jsonify({
                "success": False,
                "message": "Usuário não encontrado após atualização"
            }), 404

        # Atualiza a sessão
        updated_user = User(
            id=updated_user_data["id"],
            nome=updated_user_data["nome"],
            email=updated_user_data["email"],
            cpf=updated_user_data["cpf"],
            nivel=updated_user_data["nivel"],
            avatar=updated_user_data["avatar"]
        )
        login_user(updated_user, remember=True)

        return jsonify({
            "success": True,
            "message": "Perfil atualizado com sucesso!",
            "avatar_url": url_for("static", filename=updated_user_data["avatar"]) if updated_user_data["avatar"] else None,
            "user_data": {
                "nome": updated_user_data["nome"],
                "email": updated_user_data["email"]
            }
        })

    except Exception as e:
        from core.extensions import app
        app.logger.error(f"Erro ao atualizar perfil: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Erro ao atualizar perfil. Por favor, tente novamente."
        }), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()