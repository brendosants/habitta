from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def nivel_requerido(nivel_necessario):
    """Decorator para restringir acesso por nível de usuário"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.nivel != nivel_necessario:
                flash("Acesso não autorizado", "danger")
                return redirect(url_for("main.index"))  # Alterado para usar blueprint
            return f(*args, **kwargs)
        return decorated_function
    return decorator