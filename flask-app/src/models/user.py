"""User model for storing user data"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from src.database import db

class User(db.Model, UserMixin):
    """User model for storing user data"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    # User profile data
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(200))
    
    # User stats
    points = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    prediction_accuracy = db.Column(db.Float, default=0.0)
    matches_participated = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    
    # Relationships
    teams = db.relationship('Team', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    def __init__(self, username, email, password=None):
        self.username = username
        self.email = email
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Return user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def __repr__(self):
        return f'<User {self.username}>'
