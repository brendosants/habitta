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
from io import StringIO, BytesIO
import openpyxl

estabelecimentos_bp = Blueprint(
    "estabelecimentos", __name__, url_prefix="/estabelecimentos"
)


# Helper function para redirecionamento
def get_redirect_url():
    return url_for("estabelecimentos.listar")


@estabelecimentos_bp.route("/listar")
@login_required
@nivel_requerido("comum")
def listar():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, nome, tipo, bairro, faixa_min, faixa_max FROM estabelecimentos"
    )
    estabelecimentos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "pages/estabelecimentos/listar.html",
        usuario=current_user,
        active_page="estabelecimentos",
        estabelecimentos=estabelecimentos,
    )


@estabelecimentos_bp.route("/novo", methods=["GET", "POST"])
@login_required
@nivel_requerido("comum")
def novo():
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar TODOS os tipos da tabela de tipos
        cursor.execute("SELECT nome FROM tipos_estabelecimento ORDER BY nome")
        tipos = [row['nome'] for row in cursor.fetchall()]
        
        if request.method == "POST":
            try:
                # Obter e validar dados
                nome = request.form.get("nome", "").strip()
                if not nome:
                    flash("Nome do estabelecimento é obrigatório", "danger")
                    return render_template(
                        "pages/estabelecimentos/novo.html",
                        usuario=current_user,
                        active_page="estabelecimentos",
                        estabelecimento=request.form,
                        tipos=tipos
                    )

                tipo = request.form.get("tipo", "")
                bairro = request.form.get("bairro", "").strip()
                try:
                    faixa_min = float(request.form.get("faixa_min", 0))
                    faixa_max = float(request.form.get("faixa_max", 0))
                    valor_medio = float(request.form.get("valor_medio", 0))
                except ValueError:
                    flash("Valores numéricos inválidos", "danger")
                    return render_template(
                        "pages/estabelecimentos/novo.html",
                        usuario=current_user,
                        active_page="estabelecimentos",
                        estabelecimento=request.form,
                        tipos=tipos
                    )

                contato_nome = request.form.get("contato_nome", "").strip()
                contato_telefone = request.form.get("contato_telefone", "").strip()
                observacoes = request.form.get("observacoes", "").strip()

                cursor.execute(
                    """
                    INSERT INTO estabelecimentos 
                    (nome, tipo, bairro, faixa_min, faixa_max, valor_medio, 
                     contato_nome, contato_telefone, observacoes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        nome,
                        tipo,
                        bairro,
                        faixa_min,
                        faixa_max,
                        valor_medio,
                        contato_nome,
                        contato_telefone,
                        observacoes,
                    ),
                )

                conn.commit()
                flash("Estabelecimento salvo com sucesso!", "success")
                return redirect(get_redirect_url())

            except Exception as e:
                print(f"Erro ao cadastrar estabelecimento: {str(e)}")
                flash("Erro ao cadastrar estabelecimento", "danger")
                return render_template(
                    "pages/estabelecimentos/novo.html",
                    usuario=current_user,
                    active_page="estabelecimentos",
                    estabelecimento=request.form,
                    tipos=tipos
                )

    except Exception as e:
        print(f"Erro de conexão: {str(e)}")
        flash("Erro de conexão com o banco de dados", "danger")
        return redirect(url_for("estabelecimentos.novo"))
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template(
        "pages/estabelecimentos/novo.html",
        usuario=current_user,
        active_page="estabelecimentos",
        estabelecimento={},
        tipos=tipos  # Passar os tipos para o template
    )

@estabelecimentos_bp.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM estabelecimentos WHERE id = %s", (id,))
        conn.commit()

        flash("Estabelecimento excluído com sucesso!", "success")
        return jsonify(
            {
                "success": True,
                "redirect_url": url_for("estabelecimentos.listar", _external=True),
            }
        )

    except Exception as e:
        print(f"Erro ao excluir: {str(e)}")
        return (
            jsonify({"success": False, "message": "Erro ao excluir estabelecimento"}),
            500,
        )

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@estabelecimentos_bp.route("/<int:id>/modal")
def ver_modal(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM estabelecimentos WHERE id = %s", (id,))
        estabelecimento = cursor.fetchone()

        if not estabelecimento:
            return (
                "<div class='alert alert-danger'>Estabelecimento não encontrado</div>",
                404,
            )

        return render_template(
            "modals/ver_estabelecimento.html", estabelecimento=estabelecimento
        )

    except Exception as e:
        return f"<div class='alert alert-danger'>Erro: {str(e)}</div>", 500

    finally:
        cursor.close()
        conn.close()


@estabelecimentos_bp.route("/editar/<int:id>/modal")
def editar_modal(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM estabelecimentos WHERE id = %s", (id,))
        estabelecimento = cursor.fetchone()

        if not estabelecimento:
            return (
                "<div class='alert alert-danger'>Estabelecimento não encontrado</div>",
                404,
            )

        return render_template(
            "modals/editar_estabelecimento.html", estabelecimento=estabelecimento
        )

    except Exception as e:
        return f"<div class='alert alert-danger'>Erro: {str(e)}</div>", 500

    finally:
        cursor.close()
        conn.close()


@estabelecimentos_bp.route("/editar/<int:id>", methods=["POST"])
def atualizar(id):
    try:
        dados = {
            "nome": request.form.get("nome"),
            "tipo": request.form.get("tipo"),
            "bairro": request.form.get("bairro"),
            "faixa_min": request.form.get("faixa_min"),
            "valor_medio": request.form.get("valor_medio"),
            "faixa_max": request.form.get("faixa_max"),
            "contato_nome": request.form.get("contato_nome"),
            "contato_telefone": request.form.get("contato_telefone"),
            "observacoes": request.form.get("observacoes"),
        }

        if not dados["nome"] or not dados["tipo"]:
            return (
                jsonify({"success": False, "message": "Nome e tipo são obrigatórios"}),
                400,
            )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE estabelecimentos 
            SET nome = %s, tipo = %s, bairro = %s, 
                faixa_min = %s, valor_medio = %s, faixa_max = %s,
                contato_nome = %s, contato_telefone = %s, observacoes = %s
            WHERE id = %s
            """,
            (
                dados["nome"],
                dados["tipo"],
                dados["bairro"],
                dados["faixa_min"],
                dados["valor_medio"],
                dados["faixa_max"],
                dados["contato_nome"],
                dados["contato_telefone"],
                dados["observacoes"],
                id,
            ),
        )
        conn.commit()

        return jsonify(
            {
                "success": True,
                "message": "Estabelecimento atualizado com sucesso!",
                "redirect_url": url_for("estabelecimentos.listar"),
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


@estabelecimentos_bp.route("/exportar/<formato>")
def exportar(formato):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT nome, tipo, bairro, faixa_min, faixa_max FROM estabelecimentos"
    )
    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    if formato == "csv":
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(
            ["Nome", "Tipo", "Bairro", "Faixa Mínima (R$)", "Faixa Máxima (R$)"]
        )

        for est in dados:
            cw.writerow(
                [
                    est["nome"],
                    est["tipo"],
                    est["bairro"],
                    f"{est['faixa_min']:.2f}",
                    f"{est['faixa_max']:.2f}",
                ]
            )

        output = make_response(si.getvalue())
        output.headers["Content-type"] = "text/csv"
        output.headers["Content-Disposition"] = (
            "attachment; filename=estabelecimentos.csv"
        )
        return output

    elif formato == "excel":
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Estabelecimentos"
        ws.append(["Nome", "Tipo", "Bairro", "Faixa Mínima (R$)", "Faixa Máxima (R$)"])

        for est in dados:
            ws.append(
                [
                    est["nome"],
                    est["tipo"],
                    est["bairro"],
                    float(est["faixa_min"]),
                    float(est["faixa_max"]),
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
            "attachment; filename=estabelecimentos.xlsx"
        )
        return output

    return redirect(get_redirect_url())
