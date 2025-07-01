import os
from flask import Blueprint, request, redirect, url_for, flash, session, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app.services.db import get_db_connection

uploads_bp = Blueprint('uploads', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@uploads_bp.route('/upload', methods=['POST'])
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO arquivo (nome_arquivo, caminho, usuario_id, setor) VALUES (%s, %s, %s, %s)",
            (filename, caminho, session['user_id'], session.get('user_setor', ''))
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Arquivo enviado com sucesso!")
    else:
        flash("Arquivo não permitido.")
    return redirect(url_for('main.dashboard'))

@uploads_bp.route('/download/<int:arquivo_id>')
def download_arquivo(arquivo_id):
    if 'user_id' not in session:
        flash("Faça login para baixar arquivos.")
        return redirect(url_for('auth.login'))
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
