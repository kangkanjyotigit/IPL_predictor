"""Populate players data"""
import logging
import random
from datetime import datetime
from .base_populator import BasePopulator
from src.models import Player, Team
from .config import (
    PLAYERS_PER_TEAM,
    PLAYER_TYPES,
    CREDIT_RANGES,
    FORM_RANGES,
    TOP_TEAMS
)

logger = logging.getLogger(__name__)

class PlayersPopulator(BasePopulator):
    """Class to populate players data"""
    
    def __init__(self):
        super().__init__()
        self.player_names = {
            'India': [
                'Virat Kohli', 'Rohit Sharma', 'KL Rahul', 'Jasprit Bumrah',
                'Ravindra Jadeja', 'Hardik Pandya', 'Mohammed Shami',
                'Rishabh Pant', 'Shubman Gill', 'Mohammed Siraj'
            ],
            'Australia': [
                'Steve Smith', 'David Warner', 'Pat Cummins', 'Mitchell Starc',
                'Glenn Maxwell', 'Josh Hazlewood', 'Cameron Green',
                'Alex Carey', 'Travis Head', 'Nathan Lyon'
            ],
            'England': [
                'Joe Root', 'Ben Stokes', 'Jos Buttler', 'James Anderson',
                'Stuart Broad', 'Jonny Bairstow', 'Moeen Ali',
                'Chris Woakes', 'Ollie Pope', 'Mark Wood'
            ]
            # Add more players for other teams
        }
    
    def _generate_player_data(self, country, player_name=None):
        """Generate data for a single player"""
        player_type = random.choice(PLAYER_TYPES)
        credit_range = CREDIT_RANGES[player_type]
        form_range = FORM_RANGES[player_type]
        
        return {
            'name': player_name or f"{country} Player {random.randint(1, 100)}",
            'country': country,
            'player_type': player_type,
            'current_credit': round(random.uniform(*credit_range), 1),
            'current_form': round(random.uniform(*form_range), 2)
        }
    
    def populate(self):
        """Populate players data"""
        try:
            logger.info("Starting players population")
            
            # Clear existing players
            self.clear_table(Player)
            
            players_data = []
            total_players_per_team = sum(PLAYERS_PER_TEAM.values())
            
            # Add known players first
            for country, names in self.player_names.items():
                for name in names:
                    player_data = self._generate_player_data(country, name)
                    players_data.append(player_data)
            
            # Add additional players to meet minimum requirements
            for team in TOP_TEAMS:
                country = team['country']
                existing_players = sum(1 for p in players_data if p['country'] == country)
                needed_players = total_players_per_team - existing_players
                
                if needed_players > 0:
                    for player_type, count in PLAYERS_PER_TEAM.items():
                        existing_type_count = sum(1 for p in players_data 
                                               if p['country'] == country and p['player_type'] == player_type)
                        needed_type_players = count - existing_type_count
                        
                        for _ in range(max(0, needed_type_players)):
                            player_data = self._generate_player_data(country)
                            players_data.append(player_data)
            
            # Create player objects
            players = [Player(**data) for data in players_data]
            
            # Bulk insert players
            self.bulk_insert(players)
            
            logger.info(f"Successfully populated {len(players)} players")
            return players
            
        except Exception as e:
            logger.error(f"Error populating players: {str(e)}")
            raise
        finally:
            self.close_session()
