from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from core.utils.db_connection import get_db_connection
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

def get_total(cursor, query, params=None):
    """Função auxiliar para obter um valor de contagem do banco de dados"""
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Erro ao executar query: {query}. Erro: {str(e)}")
        return 0

@main_bp.route('/')
@login_required
def index():
    """Rota raiz que redireciona"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        total_clientes = get_total(cursor, "SELECT COUNT(*) FROM clientes")
        total_estabelecimentos_comercial = get_total(
            cursor, "SELECT COUNT(*) FROM estabelecimentos WHERE tipo = 'comercial'"
        )
        total_estabelecimentos_residencial = get_total(
            cursor, "SELECT COUNT(*) FROM estabelecimentos WHERE tipo = 'residencial'"
        )
        total_clientes_sem_ofertas = get_total(
            cursor,
            """
            SELECT COUNT(*) FROM clientes c 
            WHERE NOT EXISTS (
                SELECT 1 FROM estabelecimentos e 
                WHERE c.renda_mensal BETWEEN e.faixa_min AND e.faixa_max
            )
            """,
        )

        return render_template(
            "dashboard.html",
            usuario=current_user,
            active_page='dashboard',
            total_clientes=total_clientes,
            total_estabelecimentos_comercial=total_estabelecimentos_comercial,
            total_estabelecimentos_residencial=total_estabelecimentos_residencial,
            total_clientes_sem_ofertas=total_clientes_sem_ofertas,
        )       
        
    except Exception as e:
        logger.error(f"Erro na rota dashboard: {str(e)}")
        # Em produção, você pode redirecionar para uma página de erro
        return render_template("dashboard.html", 
                            error="Erro ao carregar dados",
                            active_page='dashboard')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()