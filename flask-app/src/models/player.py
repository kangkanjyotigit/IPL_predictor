"""Player model for storing player data"""

from datetime import datetime
from src.database import db

class Player(db.Model):
    """Player model for storing player information"""
    
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team_name = db.Column(db.String(100), nullable=False, index=True)
    role = db.Column(db.String(50), nullable=False, index=True)  # batsman, bowler, all-rounder, wicket-keeper
    credit_points = db.Column(db.Float, nullable=False)
    current_form = db.Column(db.Float, default=0.0, index=True)
    
    # Performance stats
    matches_played = db.Column(db.Integer, default=0)
    batting_average = db.Column(db.Float, default=0.0)
    bowling_average = db.Column(db.Float, default=0.0)
    strike_rate = db.Column(db.Float, default=0.0)
    economy_rate = db.Column(db.Float, default=0.0)
    
    # Relationships with back_populates instead of backref
    teams = db.relationship('TeamPlayer', foreign_keys='TeamPlayer.player_id', back_populates='player_ref', overlaps="team_players")
    team_players = db.relationship('TeamPlayer', back_populates='player_ref', overlaps="teams")
    performances = db.relationship('PlayerPerformance', back_populates='player', lazy=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, team_name, role, credit_points, current_form=0.0):
        self.name = name
        self.team_name = team_name
        self.role = role
        self.credit_points = credit_points
        self.current_form = current_form
    
    def __repr__(self):
        return f'<Player {self.name}>'
    
    def calculate_points(self, runs=0, wickets=0, catches=0, stumpings=0):
        """Calculate points based on performance"""
        points = 0
        
        # Batting points
        points += runs * 1  # 1 point per run
        if runs >= 50:
            points += 8  # Bonus for half century
        if runs >= 100:
            points += 16  # Bonus for century
        
        # Bowling points
        points += wickets * 25  # 25 points per wicket
        if wickets >= 3:
            points += 8  # Bonus for 3+ wickets
        if wickets >= 5:
            points += 16  # Bonus for 5+ wickets
        
        # Fielding points
        points += catches * 8  # 8 points per catch
        points += stumpings * 12  # 12 points per stumping
        
        return points
    
    def update_form(self, match_points):
        """Update player's form based on recent performance"""
        # Simple moving average
        self.current_form = (self.current_form + match_points) / 2
        db.session.commit()


class PlayerPerformance(db.Model):
    """Model for tracking player performance in matches"""
    
    __tablename__ = 'player_performances'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False, index=True)
    
    # Match stats
    runs = db.Column(db.Integer, default=0)
    wickets = db.Column(db.Integer, default=0)
    catches = db.Column(db.Integer, default=0)
    stumpings = db.Column(db.Integer, default=0)
    
    # Dream11 points
    points = db.Column(db.Float, default=0.0)
    
    # Relationships with back_populates
    player = db.relationship('Player', back_populates='performances')
    match = db.relationship('Match', back_populates='performances')
    
    # Metadata
    match_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_points(self):
        """Calculate Dream11 points based on performance"""
        points = 0
        
        # Batting points
        points += self.runs  # 1 point per run
        if self.runs >= 50:  # Bonus for half-century
            points += 8
        if self.runs >= 100:  # Additional bonus for century
            points += 16
        
        # Bowling points
        points += self.wickets * 25  # 25 points per wicket
        if self.wickets >= 3:  # Bonus for 3+ wickets
            points += 8
        if self.wickets >= 5:  # Additional bonus for 5+ wickets
            points += 16
        
        # Fielding points
        points += self.catches * 8  # 8 points per catch
        points += self.stumpings * 12  # 12 points per stumping
        
        self.points = points
        return points
    
    def __repr__(self):
        return f'<PlayerPerformance player_id={self.player_id} match_id={self.match_id}>'
