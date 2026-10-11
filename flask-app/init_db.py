"""Initialize the database with sample data"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from flask import Flask
from src.database import db
from src.models.user import User
from src.models.match import Match
from src.models.player import Player, PlayerPerformance
from src.models.team import Team, TeamPlayer
from src.models.venue import Venue

def init_db():
    # Create Flask app
    app = Flask(__name__, 
               template_folder='src/frontend/templates',
               static_folder='src/frontend/static')

    # Configure app
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dream11_prediction.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create venues
        venues_data = [
            {"name": "M.Chinnaswamy Stadium"},
            {"name": "Eden Gardens"},
            {"name": "Wankhede Stadium"},
            {"name": "Feroz Shah Kotla"},
            {"name": "MA Chidambaram Stadium"}
        ]
        
        venues = []
        for venue_data in venues_data:
            venue = Venue(name=venue_data["name"])
            db.session.add(venue)
            venues.append(venue)
        
        # Commit to get IDs for venues
        db.session.commit()
        
        # Create matches
        matches_data = [
            {
                "team1": "Royal Challengers Bangalore",
                "team2": "Mumbai Indians",
                "date": datetime.now() + timedelta(days=1),
                "status": "upcoming"
            },
            {
                "team1": "Chennai Super Kings",
                "team2": "Kolkata Knight Riders",
                "date": datetime.now() + timedelta(days=2),
                "status": "upcoming"
            },
            {
                "team1": "Delhi Capitals",
                "team2": "Rajasthan Royals",
                "date": datetime.now() - timedelta(days=1),
                "status": "completed",
                "team1_score": "186/4",
                "team2_score": "172/8",
                "winner": "Delhi Capitals"
            }
        ]
        
        matches = []
        for i, match_data in enumerate(matches_data):
            match = Match(
                team1=match_data["team1"],
                team2=match_data["team2"],
                date=match_data["date"],
                venue_id=venues[i % len(venues)].id,
                status=match_data["status"]
            )
            if "team1_score" in match_data:
                match.team1_score = match_data["team1_score"]
            if "team2_score" in match_data:
                match.team2_score = match_data["team2_score"]
            if "winner" in match_data:
                match.winner = match_data["winner"]
            
            db.session.add(match)
            matches.append(match)
        
        # Commit to get IDs for matches
        db.session.commit()
        
        # Create players
        players_data = [
            {"name": "Virat Kohli", "team_name": "RCB", "role": "Batsman", "credit_points": 12.5},
            {"name": "Rohit Sharma", "team_name": "MI", "role": "Batsman", "credit_points": 12.0},
            {"name": "MS Dhoni", "team_name": "CSK", "role": "Wicket-keeper", "credit_points": 11.0},
            {"name": "Jasprit Bumrah", "team_name": "MI", "role": "Bowler", "credit_points": 11.5},
            {"name": "Ravindra Jadeja", "team_name": "CSK", "role": "All-rounder", "credit_points": 10.5},
            {"name": "KL Rahul", "team_name": "LSG", "role": "Batsman", "credit_points": 11.0},
            {"name": "Rishabh Pant", "team_name": "DC", "role": "Wicket-keeper", "credit_points": 10.5},
            {"name": "Hardik Pandya", "team_name": "GT", "role": "All-rounder", "credit_points": 11.0},
            {"name": "Yuzvendra Chahal", "team_name": "RR", "role": "Bowler", "credit_points": 10.0},
            {"name": "Rashid Khan", "team_name": "GT", "role": "Bowler", "credit_points": 11.0}
        ]
        
        players = []
        for player_data in players_data:
            player = Player(
                name=player_data["name"],
                team_name=player_data["team_name"],
                role=player_data["role"],
                credit_points=player_data["credit_points"]
            )
            db.session.add(player)
            players.append(player)
        
        # Commit to get IDs for players
        db.session.commit()
        
        # Create test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            password=generate_password_hash("password123")
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Create sample user team
        if players and matches:
            team = Team(
                name="Test Dream Team",
                user_id=test_user.id,
                match_id=matches[0].id,
                captain_id=players[0].id,
                vice_captain_id=players[1].id
            )
            db.session.add(team)
            db.session.flush()
            
            # Add players to team
            for i in range(min(11, len(players))):
                team_player = TeamPlayer(
                    team_id=team.id,
                    player_id=players[i].id
                )
                db.session.add(team_player)
        
        # Commit all changes
        try:
            db.session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing database: {str(e)}")

if __name__ == "__main__":
    init_db()
