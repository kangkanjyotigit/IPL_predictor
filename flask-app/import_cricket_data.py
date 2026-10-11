"""
Cricbuzz Match Data Importer Script

This script uses the RapidAPI Cricbuzz API to fetch real cricket match data
and import it into the Dream11 Prediction app's database.
"""

from app import app, db
from src.models import Match, Player, Venue
from src.services.api_service import CricbuzzAPI, MatchImporter
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_cricbuzz_data():
    """Import real cricket match data from Cricbuzz API"""
    
    # Initialize the API with your RapidAPI key
    api_key = os.environ["RAPIDAPI_KEY"]  # Your RapidAPI key
    
    logger.info("Initializing Cricbuzz API with provided key")
    cricbuzz_api = CricbuzzAPI(api_key=api_key)
    
    # Create a match importer
    match_importer = MatchImporter(
        api_service=cricbuzz_api,
        db=db,
        Player=Player,
        Match=Match,
        Venue=Venue
    )
    
    # Import match data within app context
    with app.app_context():
        logger.info("Importing recent IPL matches...")
        try:
            # First try to import IPL matches (ID may change based on latest season)
            ipl_matches_count = match_importer.import_ipl_matches()
            logger.info(f"Imported {ipl_matches_count} IPL matches")
            
            # If no IPL matches found, import upcoming matches
            if ipl_matches_count == 0:
                logger.info("No IPL matches found. Importing upcoming matches...")
                upcoming_count = match_importer.import_upcoming_matches()
                logger.info(f"Imported {upcoming_count} upcoming matches")
        
        except Exception as e:
            logger.error(f"Error importing matches: {str(e)}")
            # If the API fails, ensure we still have sample data
            logger.info("Using sample data from mock API")
            sample_data = cricbuzz_api.get_mock_matches()
            
            # Process and store the sample data
            for match_data in sample_data.get("typeMatches", []):
                for match_info in match_data.get("seriesMatches", []):
                    for match in match_info.get("seriesAdWrapper", {}).get("matches", []):
                        try:
                            match_id = match.get("matchInfo", {}).get("matchId")
                            if match_id:
                                logger.info(f"Processing sample match ID: {match_id}")
                                match_importer._import_match(match_id)
                        except Exception as e:
                            logger.error(f"Error importing sample match: {str(e)}")
        
        # Count matches in database
        matches_count = Match.query.count()
        logger.info(f"Total matches in database: {matches_count}")
        
        # Count players in database
        players_count = Player.query.count()
        logger.info(f"Total players in database: {players_count}")
        
        # Count venues in database
        venues_count = Venue.query.count()
        logger.info(f"Total venues in database: {venues_count}")
        
        logger.info("Data import completed successfully")

if __name__ == "__main__":
    import_cricbuzz_data()
