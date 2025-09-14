from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

mail = Mail()
bcrypt = Bcrypt()
login_manager = LoginManager()

def init_app(app):
    """Inicializa todas as extensões"""
    mail.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.tela_login'
    
    # Configurações adicionais
    from core.utils import logging, file_handlers
    logging.configure_logging(app)
    file_handlers.configure_avatar_handler(app)