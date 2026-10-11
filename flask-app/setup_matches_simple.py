"""
Simple match setup script
Creates cricket matches and players with proper field names checked from the database
"""

from app import app, db
from src.models import Match, Player, Team, User, Venue
from datetime import datetime, timedelta
import random
import inspect
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inspect_model(model_class):
    """Inspect a model to get its fields"""
    logger.info(f"Inspecting model: {model_class.__name__}")
    init_params = inspect.signature(model_class.__init__).parameters
    fields = list(init_params.keys())
    if 'self' in fields:
        fields.remove('self')
    logger.info(f"Fields: {fields}")
    return fields

def create_sample_data():
    """Create sample data for the Dream11 app"""
    with app.app_context():
        # Clear existing data
        try:
            logger.info("Clearing existing data...")
            Match.query.delete()
            Player.query.delete()
            Venue.query.delete()
            db.session.commit()
            logger.info("Existing data cleared")
        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            db.session.rollback()
        
        # Create venues
        venues = []
        logger.info("Creating venues...")
        for venue_data in [
            {"name": "Wankhede Stadium", "city": "Mumbai", "country": "India", "capacity": 33000},
            {"name": "MA Chidambaram Stadium", "city": "Chennai", "country": "India", "capacity": 50000},
            {"name": "M. Chinnaswamy Stadium", "city": "Bangalore", "country": "India", "capacity": 40000}
        ]:
            venue = Venue(**venue_data)
            db.session.add(venue)
            venues.append(venue)
        db.session.commit()
        logger.info(f"Created {len(venues)} venues")
        
        # Create teams
        teams = ["Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
                "Delhi Capitals", "Kolkata Knight Riders", "Punjab Kings"]
        
        # Check Player model fields
        player_fields = inspect_model(Player)
        
        # Create players
        logger.info("Creating players...")
        players_created = 0
        roles = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
        
        for team in teams:
            for i in range(5):
                role = roles[i % len(roles)]
                
                # Create player with dynamic parameters based on actual model fields
                player_params = {
                    "name": f"{team[:3]}_Player{i+1}",
                    "team_name": team,
                    "role": role
                }
                
                # Add credit value with the right field name
                if "credit_points" in player_fields:
                    player_params["credit_points"] = round(random.uniform(7.0, 10.0), 1)
                elif "credit_value" in player_fields:
                    player_params["credit_value"] = round(random.uniform(7.0, 10.0), 1)
                
                # Add form with the right field name
                if "current_form" in player_fields:
                    player_params["current_form"] = round(random.uniform(0.5, 0.9), 2)
                elif "form" in player_fields:
                    player_params["form"] = round(random.uniform(0.5, 0.9), 2)
                
                player = Player(**player_params)
                db.session.add(player)
                players_created += 1
        
        db.session.commit()
        logger.info(f"Created {players_created} players")
        
        # Create matches
        logger.info("Creating matches...")
        matches_created = 0
        
        # Upcoming matches
        for i in range(5):
            team1, team2 = random.sample(teams, 2)
            match_date = datetime.now() + timedelta(days=i+1)
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
        
        # Live match
        team1, team2 = random.sample(teams, 2)
        venue = random.choice(venues)
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
        
        # Completed matches
        for i in range(3):
            team1, team2 = random.sample(teams, 2)
            match_date = datetime.now() - timedelta(days=i+1)
            venue = random.choice(venues)
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
        
        logger.info("Sample data creation completed successfully!")

if __name__ == "__main__":
    logger.info("Starting sample data creation")
    create_sample_data()
    print("✓ Sample match data created successfully!")
