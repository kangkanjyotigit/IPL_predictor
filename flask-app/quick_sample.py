"""
Quick Sample Data Generator
Creates sample matches and players directly in the database
"""

from app import app, db
from src.models import Match, Player, Venue
from datetime import datetime, timedelta
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Teams
IPL_TEAMS = [
    "Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
    "Delhi Capitals", "Kolkata Knight Riders", "Punjab Kings", 
    "Rajasthan Royals", "Sunrisers Hyderabad"
]

# Player roles
ROLES = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]

def create_sample_venue():
    """Create a sample venue"""
    venue = Venue(
        name="Wankhede Stadium",
        city="Mumbai",
        country="India",
        capacity=33000
    )
    db.session.add(venue)
    db.session.commit()
    logger.info(f"Created venue: {venue.name}")
    return venue

def create_sample_matches(venue):
    """Create sample upcoming and live matches"""
    matches_created = 0
    
    # Create upcoming matches (next 7 days)
    for i in range(5):
        team1, team2 = random.sample(IPL_TEAMS, 2)
        match_date = datetime.now() + timedelta(days=i+1)
        
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
    
    # Create a live match
    team1, team2 = random.sample(IPL_TEAMS, 2)
    match = Match(
        team1=team1,
        team2=team2,
        date=datetime.now(),
        status="live",
        venue_id=venue.id,
        format="T20",
        series_name="IPL 2025"
    )
    db.session.add(match)
    matches_created += 1
    
    db.session.commit()
    logger.info(f"Created {matches_created} matches")
    return matches_created

def create_sample_players():
    """Create sample players for all teams"""
    players_created = 0
    
    for team in IPL_TEAMS:
        for i in range(4):
            role = ROLES[i % len(ROLES)]
            player = Player(
                name=f"{team[:3]}_Player{i+1}",
                team_name=team,
                role=role
            )
            # Try to add credit_points if it exists
            try:
                player.credit_points = 8.5
            except:
                pass
                
            db.session.add(player)
            players_created += 1
    
    db.session.commit()
    logger.info(f"Created {players_created} players")
    return players_created

def main():
    """Generate sample data"""
    with app.app_context():
        logger.info("Creating sample data...")
        
        # Check existing data
        matches_count = Match.query.count()
        if matches_count > 0:
            logger.info(f"Found {matches_count} existing matches, skipping creation")
        else:
            # Create venue
            venue = Venue.query.first()
            if not venue:
                venue = create_sample_venue()
            
            # Create matches
            create_sample_matches(venue)
            
            # Create players
            if Player.query.count() == 0:
                create_sample_players()
        
        logger.info("Sample data created successfully")

if __name__ == "__main__":
    main()
    print("✓ Sample data created successfully!")
