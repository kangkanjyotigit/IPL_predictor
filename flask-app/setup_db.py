from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import os

# Create a small Flask app just for database setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define minimal models to create the database
class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    
    def __init__(self, name, city=None, country=None, capacity=None):
        self.name = name
        self.city = city
        self.country = country
        self.capacity = capacity

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team1 = db.Column(db.String(100), nullable=False)
    team2 = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='upcoming')
    result = db.Column(db.String(200))
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    external_id = db.Column(db.String(100), nullable=True, unique=True)
    format = db.Column(db.String(20), default='T20')
    series_name = db.Column(db.String(200), nullable=True)
    
    venue = db.relationship('Venue', backref=db.backref('matches', lazy=True))

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50))
    credit_value = db.Column(db.Float, default=8.0)
    current_form = db.Column(db.Float, default=0.5)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    match = db.relationship('Match', backref=db.backref('teams', lazy=True))
    user = db.relationship('User', backref=db.backref('teams', lazy=True))

# Initialize the database and add sample data
def setup_database():
    # Delete existing database file if it exists
    if os.path.exists('database.db'):
        os.remove('database.db')
        print("Removed existing database file")

    # Create all tables
    with app.app_context():
        db.create_all()
        print("Created database tables")
        
        # Add sample venues
        venues = [
            Venue(name="Wankhede Stadium", city="Mumbai", country="India", capacity=33000),
            Venue(name="Eden Gardens", city="Kolkata", country="India", capacity=66000),
            Venue(name="M. Chinnaswamy Stadium", city="Bangalore", country="India", capacity=40000),
        ]
        
        for venue in venues:
            db.session.add(venue)
        db.session.commit()
        print(f"Added {len(venues)} venues")
        
        # Add sample matches
        teams = ["Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
                "Delhi Capitals", "Kolkata Knight Riders", "Punjab Kings"]
        
        matches = []
        # Upcoming matches
        for i in range(5):
            team1, team2 = random.sample(teams, 2)
            match_date = datetime.now() + timedelta(days=i+1)
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="upcoming",
                venue_id=random.choice(venues).id,
                external_id=f"IPL2025_{i+100}",
                format="T20",
                series_name="IPL 2025"
            )
            matches.append(match)
        
        # Completed matches
        for i in range(3):
            team1, team2 = random.sample(teams, 2)
            match_date = datetime.now() - timedelta(days=i+1)
            winner = random.choice([team1, team2])
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="completed",
                result=f"{winner} won by {random.randint(1, 8)} {'wickets' if random.random() > 0.5 else 'runs'}",
                venue_id=random.choice(venues).id,
                external_id=f"IPL2025_{i+200}",
                format="T20",
                series_name="IPL 2025"
            )
            matches.append(match)
        
        for match in matches:
            db.session.add(match)
        db.session.commit()
        print(f"Added {len(matches)} matches")
        
        # Add sample players for each team
        for team in teams:
            for i in range(5):  # Just 5 players per team for simplicity
                role = random.choice(["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"])
                player = Player(
                    name=f"{team[:3]}_Player{i+1}",
                    team_name=team,
                    role=role,
                    credit_value=round(random.uniform(7.0, 10.0), 1),
                    current_form=round(random.uniform(0.4, 0.9), 2)
                )
                db.session.add(player)
        db.session.commit()
        print(f"Added sample players for all teams")
        
        # Add admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            is_admin=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Added admin user (username: admin, password: admin123)")
        
        print("Database setup completed successfully!")

if __name__ == "__main__":
    setup_database()
