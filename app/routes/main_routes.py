import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from flask import (
    Blueprint, render_template, session, redirect, url_for, 
    flash, current_app, request, send_from_directory, abort
)
from werkzeug.utils import secure_filename
from app.services.ia_service import ler_arquivo_texto, gerar_resumo_ia
from app.services.db import get_db_connection
from app.services.analysis_service import analisar_excel, analisar_word
from app.utils.validators import allowed_file, ALLOWED_EXTENSIONS
from app.utils.decorators import login_required
from app.exceptions import FileProcessingError


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    """Exibe o dashboard do usuário com seus arquivos"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM arquivo WHERE usuario_id = %s ORDER BY id DESC", 
                    (session['user_id'],)
                )
                arquivos = cursor.fetchall()
        
        return render_template(
            'dashboard.html',
            nome=session.get('user_nome'),
            arquivos=arquivos
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao acessar dashboard: {str(e)}")
        flash("Ocorreu um erro ao carregar o dashboard. Tente novamente.")
        return redirect(url_for('auth.login'))
    
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        # Aqui você faz sua autenticação
        usuario = autenticar(email, senha)
        if usuario:
            session['user_id'] = usuario.id
            session['user_nome'] = usuario.nome
            return redirect(url_for('dashboard'))  # <-- Aqui faz o redirecionamento!
        else:
            flash('Login inválido!')
            return render_template('login.html')
    else:
        return redirect(url_for('main.dashboard'))
    
def autenticar(email, senha):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM usuario WHERE email = %s AND senha = %s", (email, senha)
            )
            return cursor.fetchone()

@main_bp.route('/upload', methods=['POST'])
@login_required
def upload_arquivo():
    """Processa upload de arquivos e gera resumo com IA"""
    if 'file' not in request.files:
        flash("Nenhum arquivo enviado.")
        return redirect(url_for('main.dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash("Nenhum arquivo selecionado.")
        return redirect(url_for('main.dashboard'))
    
    if not allowed_file(file.filename):
        flash(f"Tipo de arquivo não permitido. Extensões permitidas: {', '.join(ALLOWED_EXTENSIONS)}")
        return redirect(url_for('main.dashboard'))
    
    try:
        filename = secure_filename(file.filename)
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        caminho = upload_folder / filename
        
        # Salva o arquivo temporariamente para processamento
        with NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            
            # Processamento do arquivo
            ext = Path(filename).suffix.lower()
            texto = ler_arquivo_texto(temp_file.name, ext)
            resumo = gerar_resumo_ia(texto) if texto else ''
            
            # Move o arquivo para o destino final
            Path(temp_file.name).rename(caminho)
        
        # Registra no banco de dados
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO arquivo 
                    (nome_arquivo, caminho, usuario_id, setor, resumo) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    (filename, str(caminho), session['user_id'], 
                     session.get('user_setor', ''), resumo)
                )
                conn.commit()
        
        flash("Arquivo enviado com sucesso e resumo gerado!")
        return redirect(url_for('main.dashboard'))
    
    except FileProcessingError as e:
        flash(f"Erro ao processar arquivo: {str(e)}")
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        current_app.logger.error(f"Erro no upload: {str(e)}")
        flash("Ocorreu um erro ao processar seu arquivo. Tente novamente.")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/download/<int:arquivo_id>')
@login_required
def download_arquivo(arquivo_id):
    """Permite o download de um arquivo"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM arquivo WHERE id = %s AND usuario_id = %s", 
                    (arquivo_id, session['user_id'])
                )
                arq = cursor.fetchone()
        
        if not arq:
            flash("Arquivo não encontrado ou sem permissão.")
            return redirect(url_for('main.dashboard'))
        
        caminho = Path(arq['caminho'])
        if not caminho.exists():
            flash("Arquivo não encontrado no servidor.")
            return redirect(url_for('main.dashboard'))
        
        return send_from_directory(
            caminho.parent,
            caminho.name,
            as_attachment=True,
            download_name=arq['nome_arquivo']  # Nome original para download
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao baixar arquivo: {str(e)}")
        flash("Ocorreu um erro ao baixar o arquivo. Tente novamente.")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/delete/<int:arquivo_id>', methods=['POST'])
@login_required
def delete_arquivo(arquivo_id):
    """Remove um arquivo do sistema e do banco de dados"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Busca o arquivo e verifica permissão
                cursor.execute(
                    "SELECT * FROM arquivo WHERE id = %s AND usuario_id = %s", 
                    (arquivo_id, session['user_id'])
                )
                arq = cursor.fetchone()
                
                if not arq:
                    flash("Arquivo não encontrado ou sem permissão.")
                    return redirect(url_for('main.dashboard'))
                
                # Remove o arquivo físico
                caminho = Path(arq['caminho'])
                if caminho.exists():
                    try:
                        caminho.unlink()
                    except OSError as e:
                        current_app.logger.warning(f"Erro ao remover arquivo físico: {str(e)}")
                
                # Remove do banco de dados
                cursor.execute("DELETE FROM arquivo WHERE id = %s", (arquivo_id,))
                conn.commit()
        
        flash("Arquivo excluído com sucesso!")
        return redirect(url_for('main.dashboard'))
    
    except Exception as e:
        current_app.logger.error(f"Erro ao excluir arquivo: {str(e)}")
        flash("Ocorreu um erro ao excluir o arquivo. Tente novamente.")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/gerar_resumo/<int:arquivo_id>', methods=['POST'])
@login_required
def gerar_resumo(arquivo_id):
    """Gera ou atualiza o resumo de um arquivo usando IA"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Verifica permissão e obtém arquivo
                cursor.execute(
                    "SELECT * FROM arquivo WHERE id = %s AND usuario_id = %s", 
                    (arquivo_id, session['user_id'])
                )
                arq = cursor.fetchone()
                
                if not arq:
                    flash("Arquivo não encontrado ou sem permissão.")
                    return redirect(url_for('main.dashboard'))
                
                # Processa o arquivo
                caminho = Path(arq['caminho'])
                if not caminho.exists():
                    flash("Arquivo não encontrado no servidor.")
                    return redirect(url_for('main.dashboard'))
                
                ext = caminho.suffix.lower()
                texto = ler_arquivo_texto(str(caminho), ext)
                resumo = gerar_resumo_ia(texto) if texto else "Não foi possível ler o arquivo."
                
                # Atualiza o banco
                cursor.execute(
                    "UPDATE arquivo SET resumo = %s WHERE id = %s", 
                    (resumo, arquivo_id)
                )
                conn.commit()
        
        flash("Resumo IA gerado/atualizado com sucesso!")
        return redirect(url_for('main.dashboard'))
    
    except FileProcessingError as e:
        flash(f"Erro ao processar arquivo: {str(e)}")
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar resumo: {str(e)}")
        flash("Ocorreu um erro ao gerar o resumo. Tente novamente.")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/teste_ia', methods=['GET', 'POST'])
@login_required
def teste_ia():
    """Página de teste da IA com upload temporário"""
    resumo = ""
    if request.method == "POST":
        if 'file' not in request.files:
            flash("Nenhum arquivo enviado.")
            return redirect(url_for('main.teste_ia'))
        
        file = request.files['file']
        if file.filename == '':
            flash("Nenhum arquivo selecionado.")
            return redirect(url_for('main.teste_ia'))
        
        if not allowed_file(file.filename):
            flash("Tipo de arquivo não permitido.")
            return redirect(url_for('main.teste_ia'))
        
        try:
            ext = Path(file.filename).suffix.lower()
            with NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                file.save(tmp.name)
                texto = ler_arquivo_texto(tmp.name, ext)
                resumo = gerar_resumo_ia(texto)
            Path(tmp.name).unlink()  # Remove o temporário
            
        except FileProcessingError as e:
            flash(f"Erro ao processar arquivo: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Erro no teste IA: {str(e)}")
            flash("Ocorreu um erro ao processar seu arquivo.")
    
    return render_template('teste_ia.html', resumo=resumo)

@main_bp.route('/analisar/<int:arquivo_id>', methods=['GET', 'POST'])
@login_required
def analisar_arquivo(arquivo_id):
    """Analisa um arquivo (Excel ou Word) e exibe resultados"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM arquivo WHERE id = %s AND usuario_id = %s", 
                    (arquivo_id, session['user_id'])
                )
                dados_arquivo = cursor.fetchone()
        
        if not dados_arquivo:
            flash("Arquivo não encontrado ou sem permissão.")
            return redirect(url_for('main.dashboard'))
        
        caminho = Path(dados_arquivo['caminho'])
        if not caminho.exists():
            flash("Arquivo não encontrado no servidor.")
            return redirect(url_for('main.dashboard'))
        
        ext = caminho.suffix.lower()
        if ext in ('.xlsx', '.xls'):
            resultado = analisar_excel(str(caminho), id_arquivo=arquivo_id)
        elif ext == '.docx':
            resultado = analisar_word(str(caminho))
        else:
            resultado = {"erro": "Tipo de arquivo não suportado para análise."}
        
        return render_template(
            'analise_resultado.html',
            resultado=resultado,
            arq=dados_arquivo
        )
    
    except Exception as e:
        current_app.logger.error(f"Erro na análise: {str(e)}")
        flash("Ocorreu um erro ao analisar o arquivo.")
        return redirect(url_for('main.dashboard'))