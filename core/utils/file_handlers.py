from functools import lru_cache
import os
from werkzeug.utils import secure_filename
import imghdr


def configure_avatar_handler(flask_app):
    """Configura o handler de avatar no app"""
    @lru_cache(maxsize=128)
    def get_user_avatar(user_id):
        try:
            from core.utils.db_connection import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT avatar FROM usuarios WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            return result["avatar"] if result and result["avatar"] else "assets/img/undraw_profile.svg"
        except Exception as e:
            flask_app.logger.error(f"Erro ao buscar avatar: {str(e)}")
            return "assets/img/undraw_profile.svg"
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    flask_app.jinja_env.globals.update(get_user_avatar=get_user_avatar)

@lru_cache(maxsize=128)
def get_user_avatar(user_id):
    """Obtém o avatar do usuário com cache"""
    try:
        from core.utils.db_connection import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT avatar FROM usuarios WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        return result["avatar"] if result and result["avatar"] else "assets/img/undraw_profile.svg"
    except Exception as e:
        app.logger.error(f"Erro ao buscar avatar: {str(e)}")
        return "assets/img/undraw_profile.svg"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def validate_image(stream):
    """Valida o tipo real do arquivo de imagem"""
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return "." + (format if format != "jpeg" else "jpg")

def save_avatar(file, user):
    """Salva o avatar do usuário no sistema de arquivos"""
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        raise ValueError("Formato de imagem inválido")

    file.seek(0)
    if not validate_image(file.stream):
        raise ValueError("Tipo de arquivo inválido")

    filename = secure_filename(f"user_{user.id}.{file.filename.split('.')[-1].lower()}")
    upload_path = os.path.join(app.root_path, "static", "uploads", "avatars", filename)

    os.makedirs(os.path.dirname(upload_path), exist_ok=True)

    if user.avatar:
        old_path = os.path.join(app.root_path, "static", user.avatar)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception as e:
                app.logger.error(f"Erro ao remover arquivo antigo: {str(e)}")

    file.save(upload_path)
    return f"uploads/avatars/{filename}"