"""
Script to populate the database with sample data
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the project root directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)

# Import our main app and db
import run
from run import app, db
from src.models.venue import Venue
from src.models.player import Player
from src.models.match import Match
from src.models.user import User
from src.models.team import Team, TeamPlayer
from werkzeug.security import generate_password_hash
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to populate the database"""
    with app.app_context():
        try:
            # Drop all tables to start fresh
            logger.info("Dropping all tables...")
            db.drop_all()
            
            # Create all tables
            logger.info("Creating all tables...")
            db.create_all()
            
            # Create venues
            venues = [
                {"name": "Eden Gardens", "city": "Kolkata", "country": "India", "capacity": 66000},
                {"name": "Wankhede Stadium", "city": "Mumbai", "country": "India", "capacity": 33000},
                {"name": "M. Chinnaswamy Stadium", "city": "Bangalore", "country": "India", "capacity": 40000},
                {"name": "MA Chidambaram Stadium", "city": "Chennai", "country": "India", "capacity": 50000},
                {"name": "Arun Jaitley Stadium", "city": "Delhi", "country": "India", "capacity": 41000},
                {"name": "Rajiv Gandhi International Cricket Stadium", "city": "Hyderabad", "country": "India", "capacity": 55000},
                {"name": "Punjab Cricket Association Stadium", "city": "Mohali", "country": "India", "capacity": 26000},
                {"name": "Sawai Mansingh Stadium", "city": "Jaipur", "country": "India", "capacity": 30000}
            ]
            
            created_venues = []
            for venue_data in venues:
                venue = Venue(**venue_data)
                created_venues.append(venue)
                db.session.add(venue)
            
            db.session.commit()
            logger.info(f"Created {len(created_venues)} venues")
            
            # Create players
            teams = ["Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
                    "Kolkata Knight Riders", "Delhi Capitals", "Sunrisers Hyderabad", 
                    "Punjab Kings", "Rajasthan Royals", "Gujarat Titans", "Lucknow Super Giants"]
            
            player_types = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"]
            
            players = []
            for team in teams:
                # Always create at least 11 players per team, with a balanced role distribution
                roles_distribution = {
                    "Batsman": 5,
                    "Bowler": 4,
                    "All-rounder": 1,
                    "Wicket-keeper": 1
                }
                player_idx = 1
                for role, count in roles_distribution.items():
                    for i in range(count):
                        player = Player(
                            name=f"{team} {role} {player_idx}",
                            team_name=team,
                            role=role,
                            credit_points=random.uniform(8.0, 10.0),
                            current_form=random.uniform(50.0, 100.0)
                        )
                        players.append(player)
                        db.session.add(player)
                        player_idx += 1
                # If for some reason fewer than 11, fill with random roles
                while player_idx <= 11:
                    role = random.choice(player_types)
                    player = Player(
                        name=f"{team} {role} {player_idx}",
                        team_name=team,
                        role=role,
                        credit_points=random.uniform(8.0, 10.0),
                        current_form=random.uniform(50.0, 100.0)
                    )
                    players.append(player)
                    db.session.add(player)
                    player_idx += 1
            
            db.session.commit()
            logger.info(f"Created {len(players)} players")
            
            # Create matches
            matches = []
            start_date = datetime.now()
            
            # Create upcoming matches
            for i in range(10):
                team1, team2 = random.sample(teams, 2)
                match_date = start_date + timedelta(days=i)
                venue = random.choice(created_venues)
                
                match = Match(team1=team1, team2=team2, date=match_date,
                             venue_id=venue.id, status='upcoming')
                matches.append(match)
                db.session.add(match)
            
            # Create some completed matches
            for i in range(5):
                team1, team2 = random.sample(teams, 2)
                match_date = start_date - timedelta(days=i+1)
                venue = random.choice(created_venues)
                winner_team = random.choice([team1, team2])
                
                match = Match(team1=team1, team2=team2, date=match_date,
                             venue_id=venue.id, status='completed')
                match.winner = winner_team
                match.team1_score = f"{random.randint(120, 200)}/{random.randint(0, 10)}"
                match.team2_score = f"{random.randint(120, 200)}/{random.randint(0, 10)}"
                
                matches.append(match)
                db.session.add(match)
            
            db.session.commit()
            logger.info(f"Created {len(matches)} matches")
            
            # Create users
            users = []
            
            # Create admin user
            admin = User(
                username="admin",
                email="admin@example.com"
            )
            admin.first_name = "Admin"
            admin.last_name = "User"
            admin.is_admin = True
            admin.set_password("admin123")
            users.append(admin)
            db.session.add(admin)
            
            # Create regular users
            for i in range(5):
                user = User(
                    username=f"user{i+1}",
                    email=f"user{i+1}@example.com"
                )
                user.first_name = f"User{i+1}"
                user.last_name = "Test"
                user.set_password(f"password{i+1}")
                users.append(user)
                db.session.add(user)
            
            db.session.commit()
            logger.info(f"Created {len(users)} users")
            
            # Create some teams for users
            for user in users:
                for i in range(random.randint(1, 3)):
                    match = random.choice(matches)
                    captain = random.choice(players)
                    vice_captain = random.choice([p for p in players if p.id != captain.id])
                    
                    team = Team(
                        name=f"{user.username}'s Team {i+1}",
                        user_id=user.id,
                        match_id=match.id,
                        captain_id=captain.id,
                        vice_captain_id=vice_captain.id
                    )
                    db.session.add(team)
                    db.session.flush()  # Get the team ID
                    
                    # Add players to team
                    team_players = random.sample(players, 11)
                    for j, player in enumerate(team_players):
                        is_captain = (player.id == captain.id)
                        is_vice_captain = (player.id == vice_captain.id)
                        
                        team_player = TeamPlayer(
                            team_id=team.id,
                            player_id=player.id,
                            is_captain=is_captain,
                            is_vice_captain=is_vice_captain
                        )
                        db.session.add(team_player)
            
            db.session.commit()
            logger.info("Created teams and team players")
            
            logger.info("Database populated successfully!")
            
        except Exception as e:
            logger.error(f"Error populating database: {str(e)}")
            raise

if __name__ == "__main__":
    main()
