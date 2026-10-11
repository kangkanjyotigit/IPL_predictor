"""Main script to populate all data"""
import logging
from .teams_populator import TeamsPopulator
from .venues_populator import VenuesPopulator
from .players_populator import PlayersPopulator
from .matches_populator import MatchesPopulator
from .performance_populator import PerformancePopulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def populate_all():
    """Populate all data in the correct order"""
    try:
        logger.info("Starting data population process")
        
        # 1. Populate Teams
        logger.info("Populating teams...")
        teams = TeamsPopulator().populate()
        logger.info(f"Successfully populated {len(teams)} teams")
        
        # 2. Populate Venues
        logger.info("Populating venues...")
        venues = VenuesPopulator().populate()
        logger.info(f"Successfully populated {len(venues)} venues")
        
        # 3. Populate Players
        logger.info("Populating players...")
        players = PlayersPopulator().populate()
        logger.info(f"Successfully populated {len(players)} players")
        
        # 4. Populate Matches
        logger.info("Populating matches...")
        matches = MatchesPopulator().populate()
        logger.info(f"Successfully populated {len(matches)} matches")
        
        # 5. Populate Player Performances
        logger.info("Populating player performances...")
        performances = PerformancePopulator().populate()
        logger.info(f"Successfully populated {len(performances)} performances")
        
        logger.info("Data population completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data population: {str(e)}")
        raise

if __name__ == "__main__":
    populate_all()
