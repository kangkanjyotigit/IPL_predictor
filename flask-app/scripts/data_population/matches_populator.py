"""Populate matches data"""
import logging
import random
from datetime import datetime, timedelta
from .base_populator import BasePopulator
from src.models import Match, Team, Venue
from .config import TOP_TEAMS

logger = logging.getLogger(__name__)

class MatchesPopulator(BasePopulator):
    """Class to populate matches data"""
    
    def __init__(self):
        super().__init__()
        self.start_date = datetime(2024, 1, 1)  # Start from January 2024
        self.days_between_matches = 3
        self.match_types = ['T20', 'ODI', 'Test']
        self.tournaments = ['International Series', 'World Cup', 'Champions Trophy']
    
    def _generate_match_data(self, team1, team2, venue, match_date):
        """Generate data for a single match"""
        return {
            'team1': team1.name,
            'team2': team2.name,
            'match_type': random.choice(self.match_types),
            'tournament': random.choice(self.tournaments),
            'venue_id': venue.id,
            'start_time': match_date,
            'status': 'upcoming'
        }
    
    def populate(self):
        """Populate matches data"""
        try:
            logger.info("Starting matches population")
            
            # Clear existing matches
            self.clear_table(Match)
            
            # Get all teams and venues
            teams = Team.query.all()
            venues = Venue.query.all()
            
            if not teams or not venues:
                raise ValueError("Teams and venues must be populated first")
            
            all_matches_data = []
            current_date = self.start_date
            
            # Generate matches between all teams
            for i, team1 in enumerate(teams):
                for j, team2 in enumerate(teams):
                    if i != j:  # Don't create matches between same team
                        # Randomly select venue
                        venue = random.choice(venues)
                        
                        # Generate match data
                        match_data = self._generate_match_data(
                            team1, team2, venue, current_date
                        )
                        all_matches_data.append(match_data)
                        
                        # Move to next match date
                        current_date += timedelta(days=self.days_between_matches)
            
            # Create match objects
            matches = [Match(**data) for data in all_matches_data]
            
            # Bulk insert matches
            self.bulk_insert(matches)
            
            logger.info(f"Successfully populated {len(matches)} matches")
            return matches
            
        except Exception as e:
            logger.error(f"Error populating matches: {str(e)}")
            raise
        finally:
            self.close_session()
