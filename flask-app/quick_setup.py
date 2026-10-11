"""
Quick Setup - Creates minimal but working data for the Dream11 app
"""

from app import app, db
from datetime import datetime, timedelta
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dream11():
    """Set up minimal data for the Dream11 app"""
    with app.app_context():
        # Access models directly from db metadata to avoid import issues
        Match = db.Model._decl_class_registry.get('Match')
        Player = db.Model._decl_class_registry.get('Player')
        Venue = db.Model._decl_class_registry.get('Venue')
        
        if not Match or not Player or not Venue:
            logger.error("Could not find required models in database")
            return False
        
        # Clear existing data
        logger.info("Clearing existing data...")
        db.session.query(Match).delete()
        db.session.query(Player).delete()
        db.session.query(Venue).delete()
        db.session.commit()
        
        # Create venues
        logger.info("Creating venues...")
        venues = []
        for venue_data in [
            {"name": "Wankhede Stadium", "city": "Mumbai", "country": "India", "capacity": 33000},
            {"name": "Eden Gardens", "city": "Kolkata", "country": "India", "capacity": 66000},
            {"name": "M. Chinnaswamy Stadium", "city": "Bangalore", "country": "India", "capacity": 40000}
        ]:
            venue = Venue(**venue_data)
            db.session.add(venue)
            venues.append(venue)
        db.session.commit()
        
        # List of teams
        teams = ["Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
                "Delhi Capitals", "Kolkata Knight Riders", "Punjab Kings"]
        
        # Create players with all required attributes
        logger.info("Creating players...")
        player_count = 0
        for team in teams:
            for i in range(5):
                role = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"][i % 4]
                
                # Create player kwargs dynamically based on available model fields
                player_kwargs = {"name": f"{team[:3]}_Player{i+1}", "team_name": team, "role": role}
                
                # Try to add other fields if they exist in the model
                try:
                    if hasattr(Player, 'credit_points'):
                        player_kwargs['credit_points'] = 8.5
                    if hasattr(Player, 'credit_value'):
                        player_kwargs['credit_value'] = 8.5
                    if hasattr(Player, 'current_form'):
                        player_kwargs['current_form'] = 0.75
                    
                    player = Player(**player_kwargs)
                    db.session.add(player)
                    player_count += 1
                except Exception as e:
                    logger.error(f"Error creating player: {str(e)}")
                    continue
        
        db.session.commit()
        logger.info(f"Created {player_count} players")
        
        # Create matches with only required attributes
        logger.info("Creating matches...")
        match_count = 0
        
        # Get all valid Match fields 
        match_fields = [c.key for c in Match.__table__.columns]
        logger.info(f"Match fields: {match_fields}")
        
        # Create upcoming matches
        for i in range(5):
            team1, team2 = random.sample(teams, 2)
            match_date = datetime.now() + timedelta(days=i+1)
            
            # Basic required fields
            match_kwargs = {
                "team1": team1,
                "team2": team2,
                "date": match_date,
                "status": "upcoming",
                "venue_id": random.choice(venues).id,
                "format": "T20", 
                "series_name": "IPL 2025"
            }
            
            try:
                match = Match(**match_kwargs)
                db.session.add(match)
                match_count += 1
            except Exception as e:
                logger.error(f"Error creating match: {str(e)}")
                continue
                
        db.session.commit()
        logger.info(f"Created {match_count} matches")
        
        return True

if __name__ == "__main__":
    logger.info("Starting quick setup")
    success = setup_dream11()
    
    if success:
        print("✓ Setup completed successfully!")
    else:
        print("✗ Setup failed")
