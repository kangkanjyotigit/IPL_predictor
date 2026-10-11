"""Populate venues data"""
import logging
from datetime import datetime
from .base_populator import BasePopulator
from src.models import Venue
from .config import VENUES

logger = logging.getLogger(__name__)

class VenuesPopulator(BasePopulator):
    """Class to populate venues data"""
    
    def __init__(self):
        super().__init__()
        self.venues_data = VENUES
    
    def populate(self):
        """Populate venues data"""
        try:
            logger.info("Starting venues population")
            
            # Clear existing venues
            self.clear_table(Venue)
            
            # Create venue objects
            venues = [Venue(**data) for data in self.venues_data]
            
            # Bulk insert venues
            self.bulk_insert(venues)
            
            logger.info(f"Successfully populated {len(venues)} venues")
            return venues
        
        except Exception as e:
            logger.error(f"Error populating venues: {str(e)}")
            raise
        finally:
            self.close_session()
