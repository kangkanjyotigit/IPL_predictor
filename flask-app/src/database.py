"""Database initialization and configuration"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()

def init_db():
    """Initialize the database"""
    app = Flask(__name__, instance_relative_config=True)
    # Ensure instance folder exists and use it for the SQLite DB
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'dream11_prediction.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    # Tables should be created via Alembic migrations (flask db upgrade)
    return app
