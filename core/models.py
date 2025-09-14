from flask_login import UserMixin
from core.extensions import login_manager
from core.utils.db_connection import get_db_connection

class User(UserMixin):
    def __init__(self, id, nome, email, cpf, nivel, avatar=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.cpf = cpf
        self.nivel = nivel
        self.avatar = avatar
        
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id, nome, email, cpf, nivel FROM usuarios WHERE id = %s", 
            (user_id,)
        )
        user_data = cursor.fetchone()
        
        if user_data:
            return User(
                id=user_data["id"],
                nome=user_data["nome"],
                email=user_data["email"],
                cpf=user_data["cpf"],
                nivel=user_data["nivel"]
            )
        return None
        
    finally:
        cursor.close()
        conn.close()