"""Script to populate the database with initial data"""

import logging
from src import create_app
from src.database import db
from scripts.data_population.teams_populator import TeamsPopulator
from scripts.data_population.venues_populator import VenuesPopulator
from scripts.data_population.players_populator import PlayersPopulator
from scripts.data_population.matches_populator import MatchesPopulator
from scripts.data_population.performance_populator import PerformancePopulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to populate data"""
    try:
        logger.info("Starting data population process...")
        
        # Create Flask app and push context
        app = create_app()
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Created database tables")
            
            # Initialize populators
            teams_populator = TeamsPopulator()
            venues_populator = VenuesPopulator()
            players_populator = PlayersPopulator()
            matches_populator = MatchesPopulator()
            performance_populator = PerformancePopulator()
            
            # Populate data in sequence
            teams_populator.populate()
            venues_populator.populate()
            players_populator.populate()
            matches_populator.populate()
            performance_populator.populate()
            
            logger.info("Successfully completed data population!")
            
    except Exception as e:
        logger.error(f"Error during data population: {str(e)}")
        raise

if __name__ == '__main__':
    main()
