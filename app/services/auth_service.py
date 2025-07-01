from werkzeug.security import generate_password_hash, check_password_hash
from app.services.db import get_db_connection

def cadastrar_usuario(nome, email, senha, setor):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        senha_hash = generate_password_hash(senha)
        cursor.execute(
            "INSERT INTO usuario (nome, email, senha, setor) VALUES (%s, %s, %s, %s)",
            (nome, email, senha_hash, setor)
        )
        conn.commit()
        return True
    except Exception as e:
        print("Erro ao cadastrar usuário:", e)
        return False
    finally:
        cursor.close()
        conn.close()

def autenticar_usuario(email, senha):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['senha'], senha):
            return user
        else:
            return None
    finally:
        cursor.close()
        conn.close()