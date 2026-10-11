"""Base class for data population"""
import logging
from src.database import db
from src.models import Match, Player, Team, Venue, PlayerPerformance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BasePopulator:
    """Base class for data population"""
    
    def __init__(self):
        """Initialize database connection"""
        self.session = db.session
    
    def populate(self):
        """Method to be implemented by child classes"""
        raise NotImplementedError
        
    def commit_changes(self):
        """Commit changes to database"""
        try:
            self.session.commit()
            logger.info("Successfully committed changes to database")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error committing changes: {str(e)}")
            raise
    
    def close_session(self):
        """Close database session"""
        try:
            self.session.close()
            logger.info("Closed database session")
        except Exception as e:
            logger.error(f"Error closing session: {str(e)}")
            raise
    
    def clear_table(self, model):
        """Clear all records from a table"""
        try:
            self.session.query(model).delete()
            self.session.commit()
            logger.info(f"Cleared all records from {model.__name__}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error clearing table {model.__name__}: {str(e)}")
            raise
    
    def bulk_insert(self, objects):
        """Bulk insert objects into database"""
        try:
            self.session.bulk_save_objects(objects)
            self.session.commit()
            logger.info(f"Bulk inserted {len(objects)} objects")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error bulk inserting objects: {str(e)}")
            raise
