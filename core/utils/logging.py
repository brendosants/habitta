import logging
from logging.handlers import RotatingFileHandler

def configure_logging(app):
    """Configura o sistema de logging da aplicação"""
    # Configuração do arquivo de log
    handler = RotatingFileHandler(
        'app.log',
        maxBytes=10000,
        backupCount=3
    )
    handler.setLevel(logging.INFO)
    
    # Formato das mensagens
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Adiciona o handler ao logger do app
    app.logger.addHandler(handler)
    
    # Configuração adicional (opcional)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplicação inicializada')