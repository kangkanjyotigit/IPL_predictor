"""
Create Premium Sample Data
This script creates high-quality sample cricket data without relying on any API.
It also ensures the database schema is correct with all required columns.
"""

from app import app, db
from src.models import Match, Player, Team, User, Venue
from datetime import datetime, timedelta
import random
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Team data
IPL_TEAMS = [
    {"name": "Mumbai Indians", "short": "MI", "color": "#004BA0"},
    {"name": "Chennai Super Kings", "short": "CSK", "color": "#FFFF00"},
    {"name": "Royal Challengers Bangalore", "short": "RCB", "color": "#FF0000"},
    {"name": "Kolkata Knight Riders", "short": "KKR", "color": "#3A225D"},
    {"name": "Delhi Capitals", "short": "DC", "color": "#00008B"},
    {"name": "Rajasthan Royals", "short": "RR", "color": "#FF1493"},
    {"name": "Punjab Kings", "short": "PBKS", "color": "#FF0000"},
    {"name": "Sunrisers Hyderabad", "short": "SRH", "color": "#FF8C00"},
    {"name": "Gujarat Titans", "short": "GT", "color": "#87CEEB"},
    {"name": "Lucknow Super Giants", "short": "LSG", "color": "#00FFFF"}
]

# Venue data
VENUES = [
    {"name": "Wankhede Stadium", "city": "Mumbai", "country": "India", "capacity": 33000},
    {"name": "M. A. Chidambaram Stadium", "city": "Chennai", "country": "India", "capacity": 50000},
    {"name": "M. Chinnaswamy Stadium", "city": "Bangalore", "country": "India", "capacity": 40000},
    {"name": "Eden Gardens", "city": "Kolkata", "country": "India", "capacity": 68000},
    {"name": "Arun Jaitley Stadium", "city": "Delhi", "country": "India", "capacity": 41000},
    {"name": "Sawai Mansingh Stadium", "city": "Jaipur", "country": "India", "capacity": 30000},
    {"name": "IS Bindra Stadium", "city": "Mohali", "country": "India", "capacity": 26000},
    {"name": "Rajiv Gandhi Stadium", "city": "Hyderabad", "country": "India", "capacity": 39000},
    {"name": "Narendra Modi Stadium", "city": "Ahmedabad", "country": "India", "capacity": 132000},
    {"name": "Ekana Cricket Stadium", "city": "Lucknow", "country": "India", "capacity": 50000}
]

# Player data by role
BATSMEN_NAMES = [
    "Virat Kohli", "Rohit Sharma", "KL Rahul", "David Warner", "Jos Buttler", 
    "Kane Williamson", "Shikhar Dhawan", "Quinton de Kock", "Faf du Plessis", 
    "Steve Smith", "Suryakumar Yadav", "Ruturaj Gaikwad", "Shubman Gill",
    "Devdutt Padikkal", "Prithvi Shaw", "Mayank Agarwal", "Jonny Bairstow",
    "Jason Roy", "Aaron Finch", "AB de Villiers", "Sanju Samson", "Glenn Maxwell"
]

BOWLERS_NAMES = [
    "Jasprit Bumrah", "Kagiso Rabada", "Trent Boult", "Rashid Khan", "Yuzvendra Chahal",
    "Mohammed Shami", "Bhuvneshwar Kumar", "Anrich Nortje", "T Natarajan", "Pat Cummins",
    "Arshdeep Singh", "Avesh Khan", "Deepak Chahar", "Shardul Thakur", "Umran Malik",
    "Josh Hazlewood", "Adam Zampa", "Ravi Bishnoi", "Murugan Ashwin", "Harshal Patel"
]

ALL_ROUNDERS_NAMES = [
    "Hardik Pandya", "Ravindra Jadeja", "Andre Russell", "Krunal Pandya", "Marcus Stoinis",
    "Axar Patel", "Moeen Ali", "Sam Curran", "Chris Morris", "Ben Stokes",
    "Sunil Narine", "Washington Sundar", "Mitchell Marsh", "Venkatesh Iyer",
    "Jason Holder", "Deepak Hooda", "Rahul Tewatia", "Liam Livingstone"
]

WICKET_KEEPERS_NAMES = [
    "MS Dhoni", "Rishabh Pant", "Jos Buttler", "Ishan Kishan", "Quinton de Kock",
    "Dinesh Karthik", "Nicholas Pooran", "Jonny Bairstow", "Wriddhiman Saha"
]

def recreate_tables():
    """Drop all tables and recreate them"""
    with app.app_context():
        logger.info("Dropping all tables...")
        try:
            db.drop_all()
            logger.info("All tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping tables: {str(e)}")
        
        logger.info("Creating all tables...")
        db.create_all()
        logger.info("All tables created successfully")

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
        players_created = 0
        
        # Distribute players among teams
        for team in IPL_TEAMS:
            team_name = team["name"]
            
            # Add batsmen
            for i in range(5):
                name = f"{random.choice(BATSMEN_NAMES)}"
                player = Player(
                    name=name,
                    team_name=team_name,
                    role="Batsman",
                    credit_value=round(random.uniform(8.0, 10.0), 1),
                    current_form=round(random.uniform(0.6, 0.9), 2)
                )
                db.session.add(player)
                players_created += 1
            
            # Add bowlers
            for i in range(5):
                name = f"{random.choice(BOWLERS_NAMES)}"
                player = Player(
                    name=name,
                    team_name=team_name,
                    role="Bowler",
                    credit_value=round(random.uniform(8.0, 10.0), 1),
                    current_form=round(random.uniform(0.6, 0.9), 2)
                )
                db.session.add(player)
                players_created += 1
            
            # Add all-rounders
            for i in range(3):
                name = f"{random.choice(ALL_ROUNDERS_NAMES)}"
                player = Player(
                    name=name,
                    team_name=team_name,
                    role="All-Rounder",
                    credit_value=round(random.uniform(8.5, 10.5), 1),
                    current_form=round(random.uniform(0.7, 0.95), 2)
                )
                db.session.add(player)
                players_created += 1
            
            # Add wicket-keepers
            for i in range(2):
                name = f"{random.choice(WICKET_KEEPERS_NAMES)}"
                player = Player(
                    name=name,
                    team_name=team_name,
                    role="Wicket-Keeper",
                    credit_value=round(random.uniform(8.0, 9.5), 1),
                    current_form=round(random.uniform(0.65, 0.9), 2)
                )
                db.session.add(player)
                players_created += 1
        
        db.session.commit()
        logger.info(f"Created {players_created} players")

def create_matches(venues):
    """Create match records with interesting scenarios"""
    with app.app_context():
        matches_created = 0
        teams = [team["name"] for team in IPL_TEAMS]
        
        # Create upcoming matches (next 7 days)
        for i in range(10):
            team_indices = random.sample(range(len(teams)), 2)
            team1 = teams[team_indices[0]]
            team2 = teams[team_indices[1]]
            
            match_date = datetime.now() + timedelta(days=random.randint(1, 7))
            venue = random.choice(venues)
            
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
            team_indices = random.sample(range(len(teams)), 2)
            team1 = teams[team_indices[0]]
            team2 = teams[team_indices[1]]
            
            match_date = datetime.now()
            venue = random.choice(venues)
            
            # Generate random scores
            team1_score = f"{random.randint(50, 180)}/{random.randint(1, 6)}"
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="live",
                venue_id=venue.id,
                format="T20",
                series_name="IPL 2025",
                team1_score=team1_score
            )
            db.session.add(match)
            matches_created += 1
        
        # Create completed matches (past 7 days)
        for i in range(8):
            team_indices = random.sample(range(len(teams)), 2)
            team1 = teams[team_indices[0]]
            team2 = teams[team_indices[1]]
            
            match_date = datetime.now() - timedelta(days=random.randint(1, 7))
            venue = random.choice(venues)
            
            # Generate scores
            team1_score = f"{random.randint(120, 220)}/{random.randint(4, 10)}"
            team2_score = f"{random.randint(100, 210)}/{random.randint(4, 10)}"
            
            # Determine winner
            team1_runs = int(team1_score.split('/')[0])
            team2_runs = int(team2_score.split('/')[0])
            
            if team1_runs > team2_runs:
                winner = team1
                result = f"{team1} won by {team1_runs - team2_runs} runs"
            else:
                winner = team2
                wickets_left = 10 - int(team2_score.split('/')[1])
                result = f"{team2} won by {wickets_left} wickets"
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="completed",
                venue_id=venue.id,
                format="T20",
                series_name="IPL 2025",
                team1_score=team1_score,
                team2_score=team2_score,
                winner=winner,
                result=result
            )
            db.session.add(match)
            matches_created += 1
        
        db.session.commit()
        logger.info(f"Created {matches_created} matches")

def create_admin_user():
    """Create an admin user"""
    with app.app_context():
        admin = User(
            username="admin",
            email="admin@example.com",
            is_admin=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        logger.info("Created admin user (username: admin, password: admin123)")

def main():
    """Main function to create sample data"""
    logger.info("Starting creation of premium sample data")
    
    # Recreate tables
    recreate_tables()
    
    # Create venues
    venues = create_venues()
    
    # Create players
    create_players()
    
    # Create matches
    create_matches(venues)
    
    # Create admin user
    create_admin_user()
    
    logger.info("Sample data creation completed successfully")

if __name__ == "__main__":
    main()
    print("✓ Premium sample cricket data created successfully!")
