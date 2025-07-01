import os
from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../instance/config.py')
    
    from app.routes.auth_routes import auth_bp
    from app.routes.main_routes import main_bp
    from app.routes.uploads import uploads_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(uploads_bp)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

    return app