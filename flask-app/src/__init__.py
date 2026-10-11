"""Dream11 Prediction App"""

import os
from flask import Flask
from flask_login import LoginManager
from src.database import db
from src.frontend import frontend_bp

def create_app():
    """Create Flask app"""
    app = Flask(__name__, 
                instance_relative_config=True,
                static_folder='frontend/static',
                template_folder='frontend/templates')
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Configure database
    # Ensure instance folder exists and use it for the SQLite DB
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'dream11_prediction.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'frontend.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from src.models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints - use consistent URL prefix with run.py
    app.register_blueprint(frontend_bp, url_prefix='/')
    
    return app
