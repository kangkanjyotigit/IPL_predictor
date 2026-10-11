"""Venue model for storing venue data"""

from datetime import datetime
from src.database import db

class Venue(db.Model):
    """Venue model for storing venue information"""
    
    __tablename__ = 'venues'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    pitch_type = db.Column(db.String(50))  # batting, bowling, balanced
    average_first_innings_score = db.Column(db.Integer)
    
    # Relationships with back_populates
    matches = db.relationship('Match', back_populates='venue', lazy='dynamic')
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, city=None, country=None, capacity=None, pitch_type=None):
        self.name = name
        self.city = city
        self.country = country
        self.capacity = capacity
        self.pitch_type = pitch_type
    
    def __repr__(self):
        return f'<Venue {self.name}>'
