#!/usr/bin/env python
"""
Script to update cricket data from external API sources.
Run this to fetch the latest match and player data.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

from flask import Flask
from src.database import db
from src.models.player import Player
from src.models.match import Match
from src.models.venue import Venue
from src.services.api_service import CricbuzzAPI, MatchImporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, 'logs', 'data_update.log'))
    ]
)
logger = logging.getLogger(__name__)

# Create a minimal Flask app for database operations
app = Flask(__name__)

# Configure app with proper database URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(project_root, 'dream11_prediction.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def update_cricket_data(match_type='upcoming', force_refresh=False):
    """Update cricket data from external APIs
    
    Args:
        match_type: Type of matches to update (upcoming, live, all)
        force_refresh: Force refresh even if data is not stale
    """
    with app.app_context():
        try:
            # Initialize database
            db.init_app(app)
            
            # Initialize API service
            api_service = CricbuzzAPI()
            
            # Initialize match importer
            match_importer = MatchImporter(api_service, db, Player, Match, Venue)
            
            # Log start of update
            logger.info(f"Starting cricket data update for {match_type} matches")
            
            # Import matches based on type
            if match_type == 'upcoming':
                matches_imported = match_importer.import_upcoming_matches()
                logger.info(f"Imported {matches_imported} upcoming matches")
            elif match_type == 'ipl':
                matches_imported = match_importer.import_ipl_matches()
                logger.info(f"Imported {matches_imported} IPL matches")
            elif match_type == 'live':
                # Implement live match update if needed
                logger.info("Live match update not implemented yet")
            elif match_type == 'all':
                matches_imported = match_importer.import_upcoming_matches()
                ipl_matches = match_importer.import_ipl_matches()
                logger.info(f"Imported {matches_imported + ipl_matches} matches in total")
            
            # Log completion
            logger.info("Cricket data update completed successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error updating cricket data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
def update_ipl_matches():
    """Update IPL match data specifically
    
    This function is designed to be called by a scheduler
    to keep IPL matches up to date
    """
    logger.info("Scheduled IPL match data update starting")
    return update_cricket_data(match_type='ipl')

def main():
    """Main function to run the script"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Update cricket data from external APIs')
    parser.add_argument('--match-type', choices=['upcoming', 'live', 'all', 'ipl'], default='all',
                       help='Type of matches to update (default: all)')
    parser.add_argument('--force', action='store_true',
                       help='Force refresh even if data is not stale')
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.join(project_root, 'logs'), exist_ok=True)
    
    # Run update
    success = update_cricket_data(args.match_type, args.force)
    
    # Return status code
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
