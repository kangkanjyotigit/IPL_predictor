"""
Create sample cricket matches and players for the Dream11 Prediction app
"""

from app import app, db
from src.models import Match, Player, Team, User, Venue
from datetime import datetime, timedelta
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Team data
IPL_TEAMS = [
    "Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
    "Delhi Capitals", "Kolkata Knight Riders", "Punjab Kings", 
    "Rajasthan Royals", "Sunrisers Hyderabad", "Gujarat Titans", "Lucknow Super Giants"
]

# Venue data
VENUES = [
    {"name": "Wankhede Stadium", "city": "Mumbai", "country": "India", "capacity": 33000},
    {"name": "MA Chidambaram Stadium", "city": "Chennai", "country": "India", "capacity": 50000},
    {"name": "M. Chinnaswamy Stadium", "city": "Bangalore", "country": "India", "capacity": 40000},
    {"name": "Eden Gardens", "city": "Kolkata", "country": "India", "capacity": 66000},
    {"name": "Arun Jaitley Stadium", "city": "Delhi", "country": "India", "capacity": 41000}
]

def reset_database():
    """Reset the database by recreating all tables"""
    with app.app_context():
        # Drop all tables
        logger.info("Dropping all tables...")
        db.drop_all()
        
        # Create all tables
        logger.info("Creating all tables...")
        db.create_all()
        logger.info("Database reset successful")

def create_venues():
    """Create venue records"""
    with app.app_context():
        venues = []
        for venue_data in VENUES:
            venue = Venue(**venue_data)
            db.session.add(venue)
            venues.append(venue)
        
        db.session.commit()
        logger.info(f"Created {len(venues)} venues")
        return venues

def create_players():
    """Create player records for all teams"""
    with app.app_context():
        roles = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
        players_created = 0
        
        for team_name in IPL_TEAMS:
            # Create 15 players per team (typical squad size)
            for i in range(15):
                role = roles[i % len(roles)]
                
                # Try to use the proper field names based on our Player model
                try:
                    # First attempt with common field names
                    player = Player(
                        name=f"{team_name[:3]}_Player{i+1}",
                        team_name=team_name,
                        role=role,
                        current_form=round(random.uniform(0.5, 0.9), 2)
                    )
                    
                    # Add optional fields if they exist in the model
                    if hasattr(Player, 'credit_value'):
                        player.credit_value = round(random.uniform(7.0, 10.5), 1)
                    
                    db.session.add(player)
                    players_created += 1
                except Exception as e:
                    logger.error(f"Error creating player: {str(e)}")
        
        db.session.commit()
        logger.info(f"Created {players_created} players")

def create_matches(venues):
    """Create match records"""
    with app.app_context():
        matches_created = 0
        
        # Create upcoming matches (next 7 days)
        for i in range(10):
            team1, team2 = random.sample(IPL_TEAMS, 2)
            venue = random.choice(venues)
            match_date = datetime.now() + timedelta(days=random.randint(1, 7))
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="upcoming",
                venue_id=venue.id,
                format="T20",
                series_name="IPL 2025"
            )
            db.session.add(match)
            matches_created += 1
        
        # Create live matches (happening now)
        for i in range(2):
            team1, team2 = random.sample(IPL_TEAMS, 2)
            venue = random.choice(venues)
            match_date = datetime.now()
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="live",
                venue_id=venue.id,
                format="T20",
                series_name="IPL 2025"
            )
            db.session.add(match)
            matches_created += 1
        
        # Create completed matches (past 7 days)
        for i in range(5):
            team1, team2 = random.sample(IPL_TEAMS, 2)
            venue = random.choice(venues)
            match_date = datetime.now() - timedelta(days=random.randint(1, 7))
            winner = random.choice([team1, team2])
            
            if winner == team1:
                result = f"{team1} won by {random.randint(1, 8)} runs"
            else:
                result = f"{team2} won by {random.randint(1, 6)} wickets"
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="completed",
                result=result,
                venue_id=venue.id,
                format="T20",
                series_name="IPL 2025"
            )
            db.session.add(match)
            matches_created += 1
        
        db.session.commit()
        logger.info(f"Created {matches_created} matches")

def create_admin_user():
    """Create an admin user"""
    with app.app_context():
        # Check if the User model has a set_password method
        admin = User(
            username="admin",
            email="admin@example.com",
            is_admin=True
        )
        
        # Try different ways to set password
        try:
            # First try the standard method
            admin.set_password("admin123")
        except Exception:
            try:
                # Then try direct assignment
                admin.password_hash = "admin123"
            except Exception as e:
                logger.error(f"Could not set admin password: {str(e)}")
        
        db.session.add(admin)
        db.session.commit()
        logger.info("Created admin user (username: admin, password: admin123)")

def main():
    """Main function to create sample data"""
    logger.info("Starting sample data creation...")
    
    # Reset database
    reset_database()
    
    # Create venues
    venues = create_venues()
    
    # Create players
    create_players()
    
    # Create matches
    create_matches(venues)
    
    # Create admin user
    create_admin_user()
    
    logger.info("Sample data creation completed!")
    print("Database successfully populated with cricket matches and players!")

if __name__ == "__main__":
    main()
