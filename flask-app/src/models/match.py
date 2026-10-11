"""Match model for storing match data"""

from datetime import datetime
from src.database import db

class Match(db.Model):
    """Match model for storing match information"""
    
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100), nullable=True, unique=True, index=True)  # ID from external API
    team1 = db.Column(db.String(100), nullable=False)
    team2 = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, index=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    status = db.Column(db.String(20), default='upcoming', index=True)  # upcoming, live, completed
    format = db.Column(db.String(20), default='T20')  # T20, ODI, Test
    series_name = db.Column(db.String(200), nullable=True)  # Name of the series/tournament
    
    # Match stats
    team1_score = db.Column(db.String(50))
    team2_score = db.Column(db.String(50))
    winner = db.Column(db.String(100))
    result = db.Column(db.String(200))
    
    # Relationships with back_populates
    venue = db.relationship('Venue', back_populates='matches')
    user_teams = db.relationship('Team', back_populates='match', overlaps="match_ref,teams")
    performances = db.relationship('PlayerPerformance', back_populates='match', lazy=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, team1, team2, date, venue_id, status='upcoming', external_id=None, format='T20', series_name=None):
        self.team1 = team1
        self.team2 = team2
        self.date = date
        self.venue_id = venue_id
        self.status = status
        self.external_id = external_id
        self.format = format
        self.series_name = series_name
    
    def __repr__(self):
        return f'<Match {self.team1} vs {self.team2}>'
