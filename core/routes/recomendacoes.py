from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
)
from flask_login import login_required, current_user
from core.utils.db_connection import get_db_connection
import csv
from io import StringIO, BytesIO
import openpyxl

# Cria o Blueprint com prefixo '/recomendacoes'
recomendacoes_bp = Blueprint("recomendacoes", __name__)  # Nome do blueprint


# Listar Recomendações (com paginação/filtro)
@recomendacoes_bp.route("/listar")
@login_required
def listar():
    filtro = request.args.get("filtro", "todos")
    busca = request.args.get("busca", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 10

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            c.id,
            c.nome,
            c.renda_mensal,
            c.telefone,
            c.email,
            c.interesse_tipo,
            c.interesse_bairro,
            COUNT(DISTINCT r.id) AS total_recomendacoes,
            COUNT(DISTINCT e.id) AS total_ofertas
        FROM clientes c
        LEFT JOIN recomendacoes r ON r.cliente_id = c.id
        LEFT JOIN estabelecimentos e 
            ON e.faixa_min <= c.renda_mensal
            AND e.tipo = c.interesse_tipo
            AND e.bairro = c.interesse_bairro
    """
    params = []

    if busca:
        query += " WHERE c.nome LIKE %s "
        params.append(f"%{busca}%")

    query += " GROUP BY c.id "

    if filtro == "com":
        query += " HAVING total_recomendacoes > 0 "
    elif filtro == "sem":
        query += " HAVING total_recomendacoes = 0 AND total_ofertas > 0 "
    elif filtro == "sem_ofertas":
        query += " HAVING total_ofertas = 0 "

    query += " ORDER BY c.nome ASC "
    count_query = f"SELECT COUNT(*) AS total FROM ({query}) AS subquery"
    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])

    cursor.execute(query, params)
    clientes = cursor.fetchall()

    cursor.execute(count_query, params[:-2])
    total = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT
            SUM(CASE WHEN total_recomendacoes > 0 THEN 1 ELSE 0 END) AS com_recomendacao,
            SUM(CASE WHEN total_recomendacoes = 0 AND total_ofertas > 0 THEN 1 ELSE 0 END) AS sem_recomendacao,
            SUM(CASE WHEN total_ofertas = 0 THEN 1 ELSE 0 END) AS sem_ofertas,
            COUNT(*) AS total
        FROM (
            SELECT 
                c.id,
                COUNT(DISTINCT r.id) AS total_recomendacoes,
                COUNT(DISTINCT e.id) AS total_ofertas
            FROM clientes c
            LEFT JOIN recomendacoes r ON r.cliente_id = c.id
            LEFT JOIN estabelecimentos e 
                ON e.faixa_min <= c.renda_mensal
                AND e.tipo = c.interesse_tipo
                AND e.bairro = c.interesse_bairro
            GROUP BY c.id
        ) AS sub
    """
    )
    resumo = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "pages/recomendacoes/listar.html",
        clientes=clientes,
        usuario=current_user,
        active_page="recomendacoes",
        filtro=filtro,
        busca=busca,
        page=page,
        per_page=per_page,
        total=total,
        resumo=resumo,
    )

@recomendacoes_bp.route("/finalizar_selecao", methods=["POST"])
@login_required
def finalizar_selecao():
    cliente_id = request.form.get('cliente_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Atualizar status da recomendação de 'selecionar' para 'ativa'
        cursor.execute("""
            UPDATE recomendacoes 
            SET status = 'ativa', 
                data_atualizacao = CURRENT_TIMESTAMP
            WHERE cliente_id = %s AND status = 'selecionar'
        """, (cliente_id,))
        
        conn.commit()
        flash("Seleção finalizada com sucesso! ✅", "success")
        
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao finalizar seleção: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('recomendacoes.cliente', 
                          cliente_id=cliente_id, 
                          modo='ver'))

# Detalhes de um Cliente
@recomendacoes_bp.route("/cliente/<int:cliente_id>")
@login_required
def cliente(cliente_id):
    modo = request.args.get('modo')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Buscar cliente
    cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
    cliente = cursor.fetchone()
    
    # Buscar recomendações do cliente
    cursor.execute("""
        SELECT * FROM recomendacoes 
        WHERE cliente_id = %s 
        ORDER BY data DESC
    """, (cliente_id,))
    recomendacoes = cursor.fetchall()
    
    # Determinar recomendação ativa
    recomendacao = None
    if recomendacoes:
        recomendacao = recomendacoes[0]
    
    # Buscar estabelecimentos conforme o modo
    if modo == 'selecionar':
        if recomendacao:
            # Buscar TODOS estabelecimentos com info de seleção
            cursor.execute("""
                SELECT 
                    e.*,
                    CASE WHEN re.estabelecimento_id IS NOT NULL THEN 1 ELSE 0 END as selecionado
                FROM estabelecimentos e
                LEFT JOIN recomendacao_estabelecimentos re 
                    ON e.id = re.estabelecimento_id 
                    AND re.recomendacao_id = %s
                ORDER BY selecionado DESC, e.nome ASC
            """, (recomendacao['id'],))
        else:
            # Criar recomendação nova para seleção manual
            cursor.execute("""
                INSERT INTO recomendacoes (cliente_id, status) 
                VALUES (%s, 'selecionar')
            """, (cliente_id,))
            conn.commit()
            recomendacao_id = cursor.lastrowid
            
            cursor.execute("SELECT * FROM recomendacoes WHERE id = %s", (recomendacao_id,))
            recomendacao = cursor.fetchone()
            
            cursor.execute("SELECT * FROM estabelecimentos ORDER BY nome ASC")
        
        imoveis = cursor.fetchall()
        
    elif modo == 'gerar':
        # Buscar estabelecimentos compatíveis (sua lógica atual)
        cursor.execute("""
            SELECT * FROM estabelecimentos 
            WHERE tipo = %s AND bairro = %s AND faixa_min <= %s
        """, (cliente['interesse_tipo'], cliente['interesse_bairro'], cliente['renda_mensal']))
        imoveis = cursor.fetchall()
        for imovel in imoveis:
            imovel['selecionado'] = False
    
    else:
        # Modo ver - estabelecimentos da recomendação
        if recomendacao:
            cursor.execute("""
                SELECT e.*, 1 as selecionado
                FROM estabelecimentos e
                INNER JOIN recomendacao_estabelecimentos re ON e.id = re.estabelecimento_id
                WHERE re.recomendacao_id = %s
            """, (recomendacao['id'],))
            imoveis = cursor.fetchall()
        else:
            imoveis = []
    
    cursor.close()
    conn.close()
    
    return render_template("pages/recomendacoes/recomendacoes_cliente.html", 
                         cliente=cliente,
                         recomendacoes=recomendacoes,
                         recomendacao=recomendacao,
                         imoveis=imoveis,
                         modo=modo)

# Rota temporária para verificar estabelecimentos
@recomendacoes_bp.route("/debug_estabelecimentos")
@login_required
def debug_estabelecimentos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM estabelecimentos")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT * FROM estabelecimentos LIMIT 5")
    primeiros = cursor.fetchall()

    cursor.close()
    conn.close()

    return f"Total de estabelecimentos: {total}<br>Primeiros: {primeiros}"


@recomendacoes_bp.route("/selecionar_imovel", methods=["POST"])
@login_required
def selecionar_imovel():
    cliente_id = request.form.get('cliente_id')
    estabelecimento_id = request.form.get('estabelecimento_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Buscar recomendação de seleção manual do cliente
        cursor.execute("""
            SELECT id FROM recomendacoes 
            WHERE cliente_id = %s AND status = 'selecionar'
        """, (cliente_id,))
        recomendacao = cursor.fetchone()
        
        if not recomendacao:
            # Criar nova recomendação se não existir
            cursor.execute("""
                INSERT INTO recomendacoes (cliente_id, status) 
                VALUES (%s, 'selecionar')
            """, (cliente_id,))
            recomendacao_id = cursor.lastrowid
        else:
            recomendacao_id = recomendacao[0]
        
        # Inserir na tabela de junção
        cursor.execute("""
            INSERT INTO recomendacao_estabelecimentos 
            (recomendacao_id, estabelecimento_id) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE estabelecimento_id = VALUES(estabelecimento_id)
        """, (recomendacao_id, estabelecimento_id))
        
        conn.commit()
        flash("Imóvel selecionado com sucesso! ✅", "success")
        
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao selecionar imóvel: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('recomendacoes.cliente', 
                          cliente_id=cliente_id, 
                          modo='selecionar'))

@recomendacoes_bp.route("/desselecionar_imovel", methods=["POST"])
@login_required
def desselecionar_imovel():
    cliente_id = request.form.get("cliente_id")
    estabelecimento_id = request.form.get("estabelecimento_id")
    modo = request.form.get("modo")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Encontrar a recomendação de seleção manual
        cursor.execute(
            """
            SELECT id FROM recomendacoes 
            WHERE cliente_id = %s AND status = 'selecionar'
        """,
            (cliente_id,),
        )
        recomendacao = cursor.fetchone()

        if recomendacao:
            # Remover estabelecimento da recomendação
            cursor.execute(
                """
                DELETE FROM recomendacao_estabelecimentos 
                WHERE recomendacao_id = %s AND estabelecimento_id = %s
            """,
                (recomendacao[0], estabelecimento_id),
            )

            conn.commit()
            flash("Imóvel removido da seleção!", "info")
        else:
            flash("Nenhuma seleção encontrada para este cliente", "warning")

    except Exception as e:
        conn.rollback()
        flash(f"Erro ao remover imóvel: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("recomendacoes.cliente", cliente_id=cliente_id, modo=modo))

@recomendacoes_bp.route("/remover_selecao", methods=["POST"])
@login_required
def remover_selecao():
    cliente_id = request.form.get('cliente_id')
    estabelecimento_id = request.form.get('estabelecimento_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Buscar recomendação de seleção manual
        cursor.execute("""
            SELECT id FROM recomendacoes 
            WHERE cliente_id = %s AND status = 'selecionar'
        """, (cliente_id,))
        recomendacao = cursor.fetchone()
        
        if recomendacao:
            # Remover da tabela de junção
            cursor.execute("""
                DELETE FROM recomendacao_estabelecimentos 
                WHERE recomendacao_id = %s AND estabelecimento_id = %s
            """, (recomendacao[0], estabelecimento_id))
            
            conn.commit()
            flash("Imóvel removido da seleção! ❌", "info")
        else:
            flash("Nenhuma seleção encontrada", "warning")
            
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao remover: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('recomendacoes.cliente', 
                          cliente_id=cliente_id, 
                          modo='selecionar'))


# Nova Recomendação
@recomendacoes_bp.route("/cliente/<int:cliente_id>/nova", methods=["POST"])
@login_required
def nova(cliente_id):
    modo = request.form.get("modo", "gerar")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO recomendacoes (cliente_id, status)
            VALUES (%s, 'ativa')
        """,
            (cliente_id,),
        )
        recomendacao_id = cursor.lastrowid
        conn.commit()
        flash("Nova recomendação criada!", "success")
    except Exception as e:
        conn.rollback()
        flash("Erro ao criar recomendação", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(
        url_for(
            "recomendacoes.cliente",
            cliente_id=cliente_id,
            recomendacao_id=recomendacao_id,
            modo=modo,
        )
    )


# Salvar Observações
@recomendacoes_bp.route("/cliente/<int:cliente_id>/salvar", methods=["POST"])
@login_required
def salvar(cliente_id):
    recomendacao_id = request.form.get("recomendacao_id")
    observacoes = request.form.get("observacoes")
    mensagem = request.form.get("mensagem")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE recomendacoes
            SET observacoes=%s, mensagem=%s
            WHERE id=%s AND cliente_id=%s
        """,
            (observacoes, mensagem, recomendacao_id, cliente_id),
        )
        conn.commit()
        flash("Dados salvos!", "success")
    except Exception as e:
        conn.rollback()
        flash("Erro ao salvar", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(
        url_for(
            "recomendacoes.cliente",
            cliente_id=cliente_id,
            recomendacao_id=recomendacao_id,
        )
    )


@recomendacoes_bp.route("/excluir/<int:recomendacao_id>", methods=["POST"])
@login_required
def excluir(recomendacao_id):
    cliente_id = request.form.get("cliente_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Primeiro excluir os relacionamentos na tabela de junção
        cursor.execute(
            "DELETE FROM recomendacao_estabelecimentos WHERE recomendacao_id = %s",
            (recomendacao_id,),
        )

        # Depois excluir a recomendação
        cursor.execute("DELETE FROM recomendacoes WHERE id = %s", (recomendacao_id,))

        conn.commit()
        flash("Recomendação excluída com sucesso!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Erro ao excluir recomendação: {str(e)}", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("recomendacoes.cliente", cliente_id=cliente_id))


# Exportar Dados
@recomendacoes_bp.route("/exportar/<formato>")
@login_required
def exportar(formato):
    filtro = request.args.get("filtro", "todos")
    busca = request.args.get("busca", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        c.id, c.nome, c.renda_mensal, c.telefone, c.email, 
        c.interesse_tipo, c.interesse_bairro,
        COUNT(r.id) AS total_recomendacoes
    FROM clientes c
    LEFT JOIN recomendacoes r ON r.cliente_id = c.id
    """
    params = []

    if busca:
        query += " WHERE c.nome LIKE %s"
        params.append(f"%{busca}%")
    query += " GROUP BY c.id"
    if filtro == "com":
        query += " HAVING COUNT(r.id) > 0"
    elif filtro == "sem":
        query += " HAVING COUNT(r.id) = 0"

    cursor.execute(query, params)
    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    if formato == "csv":
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(
            [
                "ID",
                "Nome",
                "Renda",
                "Telefone",
                "Email",
                "Interesse",
                "Bairro",
                "Total Recomendações",
            ]
        )
        for row in dados:
            cw.writerow(
                [
                    row["id"],
                    row["nome"],
                    row["renda_mensal"],
                    row["telefone"],
                    row["email"],
                    row["interesse_tipo"],
                    row["interesse_bairro"],
                    row["total_recomendacoes"],
                ]
            )
        output = make_response(si.getvalue())
        output.headers["Content-type"] = "text/csv"
        output.headers["Content-Disposition"] = "attachment; filename=recomendacoes.csv"
        return output

    elif formato == "excel":
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(
            [
                "ID",
                "Nome",
                "Renda",
                "Telefone",
                "Email",
                "Interesse",
                "Bairro",
                "Total Recomendações",
            ]
        )
        for row in dados:
            ws.append(
                [
                    row["id"],
                    row["nome"],
                    row["renda_mensal"],
                    row["telefone"],
                    row["email"],
                    row["interesse_tipo"],
                    row["interesse_bairro"],
                    row["total_recomendacoes"],
                ]
            )
        virtual_workbook = BytesIO()
        wb.save(virtual_workbook)
        virtual_workbook.seek(0)
        output = make_response(virtual_workbook.read())
        output.headers["Content-type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        output.headers["Content-Disposition"] = (
            "attachment; filename=recomendacoes.xlsx"
        )
        return output

    return redirect(url_for("recomendacoes.listar"))
