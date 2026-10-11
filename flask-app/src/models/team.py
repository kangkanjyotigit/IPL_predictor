"""Team model for storing team data"""

from datetime import datetime
from src.database import db
from src.models.player import PlayerPerformance

class Team(db.Model):
    """Team model for storing team information"""
    
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False, index=True)
    captain_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    vice_captain_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    points = db.Column(db.Float, default=0.0)
    rank = db.Column(db.Integer)
    
    # Relationships with back_populates instead of backref
    players = db.relationship('TeamPlayer', back_populates='team', lazy=True)
    captain = db.relationship('Player', foreign_keys=[captain_id])
    vice_captain = db.relationship('Player', foreign_keys=[vice_captain_id])
    match = db.relationship('Match', back_populates='user_teams')
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, user_id, match_id, captain_id=None, vice_captain_id=None):
        self.name = name
        self.user_id = user_id
        self.match_id = match_id
        self.captain_id = captain_id
        self.vice_captain_id = vice_captain_id
    
    def __repr__(self):
        return f'<Team {self.name}>'
    
    def calculate_points(self):
        """Calculate total team points based on player performances"""
        total_points = 0
        for team_player in self.players:
            player = team_player.player_ref
            # Get player performance for this match
            performance = PlayerPerformance.query.filter_by(
                player_id=player.id, 
                match_id=self.match_id
            ).first()
            
            if performance:
                # Regular player points
                player_points = performance.points
                
                # Apply multipliers for captain and vice-captain
                if team_player.is_captain:
                    player_points *= 2
                elif team_player.is_vice_captain:
                    player_points *= 1.5
                
                total_points += player_points
        
        self.points = total_points
        return total_points


class TeamPlayer(db.Model):
    """Model for team-player associations"""
    
    __tablename__ = 'team_players'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    is_captain = db.Column(db.Boolean, default=False)
    is_vice_captain = db.Column(db.Boolean, default=False)
    
    # Relationships with back_populates instead of backref
    team = db.relationship('Team', back_populates='players', overlaps="user_teams")
    player_ref = db.relationship('Player', back_populates='team_players', overlaps="teams")
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, team_id, player_id, is_captain=False, is_vice_captain=False):
        self.team_id = team_id
        self.player_id = player_id
        self.is_captain = is_captain
        self.is_vice_captain = is_vice_captain
    
    def __repr__(self):
        return f'<TeamPlayer team_id={self.team_id} player_id={self.player_id}>'
