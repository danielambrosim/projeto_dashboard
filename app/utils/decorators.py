from functools import wraps
from flask import flash, redirect, url_for, session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Faça login para acessar esta página.")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function