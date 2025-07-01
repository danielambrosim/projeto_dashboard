import os
from flask import Blueprint, render_template, session, redirect, url_for, flash, current_app, request, send_from_directory
from werkzeug.utils import secure_filename
from app.services.ia_service import ler_arquivo_texto, gerar_resumo_ia
from app.services.db import get_db_connection

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    if 'user_id' not in session:
        flash("Faça login para acessar o dashboard.")
        return redirect(url_for('auth.login'))
    from app.services.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM arquivo WHERE usuario_id = %s", (session['user_id'],))
    arquivos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', nome=session.get('user_nome'), arquivos=arquivos)



ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'excel'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/upload', methods=['POST'])
def upload_arquivo():
    if 'user_id' not in session:
        flash("Faça login para enviar arquivos.")
        return redirect(url_for('auth.login'))
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        caminho = os.path.join(upload_folder, filename)
        file.save(caminho)

        # IA: Ler o arquivo e gerar resumo
        ext = os.path.splitext(filename)[1].lower()
        texto = ler_arquivo_texto(caminho, ext)
        resumo = gerar_resumo_ia(texto) if texto else ''

        # Registrar no banco (agora incluindo resumo!)
        from app.services.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO arquivo (nome_arquivo, caminho, usuario_id, setor, resumo) VALUES (%s, %s, %s, %s, %s)",
            (filename, caminho, session['user_id'], session.get('user_setor', ''), resumo)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Arquivo enviado com sucesso e resumo gerado!")
    else:
        flash("Arquivo não permitido.")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/download/<int:arquivo_id>')
def download_arquivo(arquivo_id):
    if 'user_id' not in session:
        flash("Faça login para baixar arquivos.")
        return redirect(url_for('auth.login'))
    from app.services.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM arquivo WHERE id = %s AND usuario_id = %s", (arquivo_id, session['user_id']))
    arq = cursor.fetchone()
    cursor.close()
    conn.close()
    if not arq:
        flash("Arquivo não encontrado ou sem permissão.")
        return redirect(url_for('main.dashboard'))
    pasta, nome = os.path.split(arq['caminho'])
    return send_from_directory(pasta, nome, as_attachment=True)

@main_bp.route('/delete/<int:arquivo_id>', methods=['POST'])
def delete_arquivo(arquivo_id):
    if 'user_id' not in session:
        flash("Faça login para excluir arquivos.")
        return redirect(url_for('auth.login'))

    # Buscar arquivo e validar dono
    from app.services.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM arquivo WHERE id = %s AND usuario_id = %s", (arquivo_id, session['user_id']))
    arq = cursor.fetchone()
    if not arq:
        cursor.close()
        conn.close()
        flash("Arquivo não encontrado ou sem permissão.")
        return redirect(url_for('main.dashboard'))

    # Tenta excluir arquivo físico
    try:
        if os.path.exists(arq['caminho']):
            os.remove(arq['caminho'])
    except Exception as e:
        flash(f"Erro ao remover arquivo: {e}")

    # Remove do banco
    cursor.execute("DELETE FROM arquivo WHERE id = %s", (arquivo_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Arquivo excluído com sucesso!")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/gerar_resumo/<int:arquivo_id>', methods=['POST'])
def gerar_resumo(arquivo_id):
    if 'user_id' not in session:
        flash("Faça login para usar a IA.")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM arquivo WHERE id = %s AND usuario_id = %s", (arquivo_id, session['user_id']))
    arq = cursor.fetchone()
    if not arq:
        cursor.close()
        conn.close()
        flash("Arquivo não encontrado ou sem permissão.")
        return redirect(url_for('main.dashboard'))

    ext = os.path.splitext(arq['nome_arquivo'])[1].lower()
    texto = ler_arquivo_texto(arq['caminho'], ext)
    resumo = gerar_resumo_ia(texto) if texto else "Arquivo sem texto lido."
    cursor.execute("UPDATE arquivo SET resumo = %s WHERE id = %s", (resumo, arquivo_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Resumo IA gerado/atualizado com sucesso!")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/teste_ia', methods=['GET', 'POST'])
def teste_ia():
    resumo = ""
    if request.method == "POST":
        file = request.files.get('file')
        if file:
            import tempfile
            ext = os.path.splitext(file.filename)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                file.save(tmp.name)
                texto = ler_arquivo_texto(tmp.name, ext)
                resumo = gerar_resumo_ia(texto)
            os.remove(tmp.name)
    return render_template('teste_ia.html', resumo=resumo)