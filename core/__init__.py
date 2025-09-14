from flask import Flask
from core.extensions import init_app

def create_app():
    app = Flask(__name__)
    
    # Configurações básicas
    app.config.from_mapping(
        SECRET_KEY='sua-chave-secreta-aqui',
        MAIL_SERVER='smtp.seuprovedor.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME='seu@email.com',
        MAIL_PASSWORD='suasenha',
        UPLOAD_FOLDER='static/uploads',
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB
    )
    
    # Inicializa extensões
    init_app(app)
    
    # Registra blueprints
    from .routes import (
        auth,
        profile,
        clientes,
        estabelecimentos,
        recomendacoes,
        main
    )
    
    app.register_blueprint(main.main_bp)
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(profile.profile_bp)
    app.register_blueprint(clientes.clientes_bp)
    app.register_blueprint(estabelecimentos.estabelecimentos_bp)
    app.register_blueprint(recomendacoes.recomendacoes_bp)
    
    return app