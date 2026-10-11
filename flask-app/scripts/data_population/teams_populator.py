"""Teams data populator"""
import logging
from .base_populator import BasePopulator
from src.models import Team
from .config import TOP_TEAMS

logger = logging.getLogger(__name__)

class TeamsPopulator(BasePopulator):
    """Class to populate teams data"""
    
    def __init__(self):
        super().__init__()
    
    def populate(self):
        """Populate teams data"""
        try:
            logger.info("Starting teams population...")
            
            # Clear existing data
            self.clear_table(Team)
            
            # Create team objects
            teams = []
            for team_data in TOP_TEAMS:
                team = Team(
                    name=team_data['name'],
                    country=team_data['country'],
                    ranking=team_data.get('ranking')
                )
                teams.append(team)
            
            # Bulk insert teams
            self.bulk_insert(teams)
            logger.info("Successfully populated teams data")
            
        except Exception as e:
            logger.error(f"Error populating teams: {str(e)}")
            raise
        finally:
            self.close_session()
