from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import cadastrar_usuario, autenticar_usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = autenticar_usuario(email, senha)
        if user:
            session['user_id'] = user['id']
            session['user_nome'] = user['nome']
            flash(f'Bem-vindo, {user["nome"]}!')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Email ou senha inválidos!')
            return render_template('login.html')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        setor = request.form['setor']
        if cadastrar_usuario(nome, email, senha, setor):
            flash('Usuário cadastrado com sucesso! Faça login.')
            return redirect(url_for('auth.login'))
        else:
            flash('Erro ao cadastrar usuário! Email já existe?')
            return render_template('register.html')
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()  # Remove tudo da sessão
    return redirect(url_for('auth.login'))