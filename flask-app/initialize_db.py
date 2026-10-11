"""
Database initialization script for Dream11 Prediction App
Creates tables and adds sample match data
"""

from app import app, db
from src.models import Match, Player, Team, User, Venue
from datetime import datetime, timedelta
import random

def initialize_database():
    """Create database tables and populate with sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Add sample venues
        venues = [
            Venue(name="Wankhede Stadium", city="Mumbai", country="India", capacity=33000),
            Venue(name="Eden Gardens", city="Kolkata", country="India", capacity=66000),
            Venue(name="M. Chinnaswamy Stadium", city="Bangalore", country="India", capacity=40000),
            Venue(name="Arun Jaitley Stadium", city="Delhi", country="India", capacity=41000),
            Venue(name="MA Chidambaram Stadium", city="Chennai", country="India", capacity=50000)
        ]
        
        for venue in venues:
            db.session.add(venue)
        
        db.session.commit()
        print(f"Added {len(venues)} sample venues")
        
        # Add sample matches
        teams = ["Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
                "Delhi Capitals", "Kolkata Knight Riders", "Punjab Kings", 
                "Rajasthan Royals", "Sunrisers Hyderabad", "Gujarat Titans", "Lucknow Super Giants"]
        
        # Create upcoming matches over the next 7 days
        upcoming_matches = []
        for i in range(10):
            team1, team2 = random.sample(teams, 2)  # Pick two random teams
            match_date = datetime.now() + timedelta(days=random.randint(1, 7))
            venue = random.choice(venues)
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="upcoming",
                venue_id=venue.id,
                external_id=f"IPL_2025_{i+100}",
                format="T20",
                series_name="IPL 2025"
            )
            upcoming_matches.append(match)
        
        # Create completed matches over the past 7 days
        completed_matches = []
        for i in range(5):
            team1, team2 = random.sample(teams, 2)  # Pick two random teams
            match_date = datetime.now() - timedelta(days=random.randint(1, 7))
            venue = random.choice(venues)
            winner = random.choice([team1, team2])
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="completed",
                result=f"{winner} won by {random.randint(1, 8)} {'wickets' if random.random() > 0.5 else 'runs'}",
                venue_id=venue.id,
                external_id=f"IPL_2025_{i+200}",
                format="T20",
                series_name="IPL 2025"
            )
            completed_matches.append(match)
        
        # Add all matches to the database
        for match in upcoming_matches + completed_matches:
            db.session.add(match)
        
        db.session.commit()
        print(f"Added {len(upcoming_matches)} upcoming matches and {len(completed_matches)} completed matches")
        
        # Add sample players for all teams
        player_roles = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
        
        for team in teams:
            for i in range(15):  # 15 players per team
                role = random.choice(player_roles)
                form = round(random.uniform(0.4, 0.9), 2)  # Current form between 0.4 and 0.9
                
                player = Player(
                    name=f"{team[:3]}_Player{i+1}",
                    team_name=team,
                    role=role,
                    credit_value=round(random.uniform(7.0, 10.5), 1),  # Credit value between 7.0 and 10.5
                    current_form=form
                )
                db.session.add(player)
        
        db.session.commit()
        print(f"Added sample players for all teams")
        
        # Add admin user if it doesn't exist
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@example.com",
                is_admin=True
            )
            admin.set_password("admin123")  # Set a default password
            db.session.add(admin)
            db.session.commit()
            print("Added admin user")
        
        print("Database initialization completed successfully!")

if __name__ == "__main__":
    initialize_database()
