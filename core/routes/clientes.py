from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    make_response,
)
from flask_login import login_required, current_user
from core.utils.db_connection import get_db_connection
from core.utils.decorators import nivel_requerido
import csv
import traceback
from io import StringIO, BytesIO
import openpyxl

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


# Helper function para redirecionamento
def get_redirect_url():
    return url_for("clientes.listar")


@clientes_bp.route("/cadastrar", methods=["GET", "POST"])
@login_required
@nivel_requerido("comum")
def cadastrar():
    if request.method == "POST":
        conn = None
        cursor = None
        try:
            dados = {
                "nome": request.form.get("nome", "").strip(),
                "renda_mensal": request.form.get("renda_mensal", "0").strip(),
                "telefone": request.form.get("telefone", "").strip(),
                "email": request.form.get("email", "").strip().lower(),
                "interesse_tipo": request.form.get("interesse_tipo", ""),
                "interesse_bairro": request.form.get("interesse_bairro", "").strip(),
            }

            # Validações
            if not dados["nome"]:
                flash("Nome do cliente é obrigatório", "danger")
                return redirect(url_for("clientes.cadastrar"))

            try:
                dados["renda_mensal"] = float(dados["renda_mensal"])
            except ValueError:
                flash("Valor de renda mensal inválido", "danger")
                return redirect(url_for("clientes.cadastrar"))

            if dados["email"] and "@" not in dados["email"]:
                flash("E-mail inválido", "danger")
                return redirect(url_for("clientes.cadastrar"))

            # Inserir no banco
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO clientes 
                (nome, renda_mensal, telefone, email, interesse_tipo, interesse_bairro)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    dados["nome"],
                    dados["renda_mensal"],
                    dados["telefone"],
                    dados["email"],
                    dados["interesse_tipo"],
                    dados["interesse_bairro"],
                ),
            )

            conn.commit()
            flash("Cliente cadastrado com sucesso!", "success")
            return redirect(get_redirect_url())

        except Exception as e:
            print(f"Erro completo: {traceback.format_exc()}")
            flash("Erro ao processar cadastro", "danger")
            return redirect(get_redirect_url())

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template(
        "pages/clientes/cadastrar.html", usuario=current_user, active_page='clientes', cliente={})


@clientes_bp.route("/listar")
@login_required
@nivel_requerido("comum")
def listar():
    filtro = request.args.get("filtro", "todos")  # Mudei de status_filtro para filtro
    busca = request.args.get("busca", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 10

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Query base
    query = """
        SELECT 
            id, nome, renda_mensal, telefone, email, 
            interesse_tipo, interesse_bairro, status
        FROM clientes
        WHERE 1=1
    """
    params = []

    # Filtro por busca (nome)
    if busca:
        query += " AND nome LIKE %s "
        params.append(f"%{busca}%")

    # Filtro por status - AGORA USANDO 'filtro'
    if filtro == "ativo":
        query += " AND status = 'ativo' "
    elif filtro == "concluido":
        query += " AND status = 'concluido' "
    elif filtro == "inativo":
        query += " AND status = 'inativo' "

    # Ordenação
    query += " ORDER BY nome ASC "

    # Query para contar total de registros (sem paginação)
    count_query = f"SELECT COUNT(*) AS total FROM clientes WHERE 1=1"
    count_params = []

    if busca:
        count_query += " AND nome LIKE %s "
        count_params.append(f"%{busca}%")

    if filtro == "ativo":
        count_query += " AND status = 'ativo' "
    elif filtro == "concluido":
        count_query += " AND status = 'concluido' "
    elif filtro == "inativo":
        count_query += " AND status = 'inativo' "

    # Aplicar paginação na query principal
    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])

    # Executar query principal
    cursor.execute(query, params)
    clientes = cursor.fetchall()
    
    # Executar query de contagem
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()["total"]

    # Contar totais por status para o resumo
    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'ativo' THEN 1 ELSE 0 END) AS ativos,
            SUM(CASE WHEN status = 'concluido' THEN 1 ELSE 0 END) AS concluidos,
            SUM(CASE WHEN status = 'inativo' THEN 1 ELSE 0 END) AS inativos
        FROM clientes
    """)
    resumo = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "pages/clientes/listar.html", 
        usuario=current_user, 
        active_page='clientes',
        filtro=filtro,  # Agora usando filtro
        busca=busca, 
        clientes=clientes,
        page=page,
        per_page=per_page,
        total=total,
        resumo=resumo
    )  
@clientes_bp.route("/<int:id>/modal")
def ver_modal(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
        cliente = cursor.fetchone()

        if not cliente:
            return "<div class='alert alert-danger'>Cliente não encontrado</div>", 404

        return render_template("modals/ver_cliente.html", cliente=cliente)

    except Exception as e:
        return f"<div class='alert alert-danger'>Erro: {str(e)}</div>", 500

    finally:
        cursor.close()
        conn.close()


@clientes_bp.route("/editar/<int:id>/modal")
def editar_modal(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
        cliente = cursor.fetchone()

        if not cliente:
            return "<div class='alert alert-danger'>Cliente não encontrado</div>", 404

        return render_template("modals/editar_cliente.html", cliente=cliente)

    except Exception as e:
        return f"<div class='alert alert-danger'>Erro: {str(e)}</div>", 500

    finally:
        cursor.close()
        conn.close()
        
@clientes_bp.route("/editar/<int:id>", methods=["POST"])
def atualizar(id):
    try:
        # Obter todos os campos do formulário
        dados = {
            "nome": request.form.get("nome"),
            "renda_mensal": request.form.get("renda_mensal"),
            "telefone": request.form.get("telefone"),
            "email": request.form.get("email"),
            "interesse_tipo": request.form.get("interesse_tipo"),
            "interesse_bairro": request.form.get("interesse_bairro"),
        }

        # Validações básicas
        if not dados["nome"] or not dados["interesse_tipo"]:
            return (
                jsonify({"success": False, "message": "Nome e tipo são obrigatórios"}),
                400,
            )

        # Atualização no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE clientes 
            SET nome = %s, renda_mensal = %s, telefone = %s, 
                email = %s, interesse_tipo = %s, interesse_bairro = %s
            WHERE id = %s
            """,
            (
                dados["nome"],
                dados["renda_mensal"],
                dados["telefone"],
                dados["email"],
                dados["interesse_tipo"],
                dados["interesse_bairro"],
                id,
            ),
        )
        conn.commit()

        return jsonify(
            {
                "success": True,
                "message": "Cliente atualizado com sucesso!",
                "redirect_url": url_for("clientes.listar"),
            }
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Erro ao atualizar: {str(e)}"}),
            500,
        )

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()




@clientes_bp.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = %s", (id,))
        conn.commit()

        flash("Cliente excluído com sucesso!", "success")
        return jsonify(
            {
                "success": True,
                "redirect_url": url_for("clientes.listar", _external=True),
            }
        )

    except Exception as e:
        print(f"Erro ao excluir: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao excluir cliente"}), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@clientes_bp.route("/exportar/<formato>")
def exportar(formato):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT nome, renda_mensal, telefone, email, interesse_tipo, interesse_bairro FROM clientes"
    )
    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    if formato == "csv":
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(
            [
                "Nome",
                "Renda Mensal (R$)",
                "Telefone",
                "Email",
                "Tipo interesse",
                "Bairro interesse",
            ]
        )

        for est in dados:
            cw.writerow(
                [
                    est["nome"],
                    est["renda_mensal"],
                    est["telefone"],
                    est["email"],
                    est["interesse_tipo"],
                    est["interesse_bairro"],
                ]
            )

        output = make_response(si.getvalue())
        output.headers["Content-type"] = "text/csv"
        output.headers["Content-Disposition"] = "attachment; filename=clientes.csv"
        return output

    elif formato == "excel":
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Clientes"
        ws.append(
            [
                "Nome",
                "Renda Mensal (R$)",
                "Telefone",
                "Email",
                "Tipo interesse",
                "Bairro interesse",
            ]
        )

        for est in dados:
            ws.append(
                [
                    est["nome"],
                    est["renda_mensal"],
                    est["telefone"],
                    est["email"],
                    est["interesse_tipo"],
                    est["interesse_bairro"],
                ]
            )

        virtual_workbook = BytesIO()
        wb.save(virtual_workbook)
        virtual_workbook.seek(0)

        output = make_response(virtual_workbook.read())
        output.headers["Content-type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        output.headers["Content-Disposition"] = "attachment; filename=clientes.xlsx"
        return output

    return redirect(get_redirect_url())
