"""Populate player performance data"""
import logging
import random
from datetime import datetime
from .base_populator import BasePopulator
from src.models import Player, Match, PlayerPerformance

logger = logging.getLogger(__name__)

class PerformancePopulator(BasePopulator):
    """Class to populate player performance data"""
    
    def _generate_batting_performance(self, player_type):
        """Generate batting performance based on player type"""
        if player_type == 'batsman':
            runs = random.randint(30, 100)
            balls = random.randint(max(20, runs), min(runs + 20, 60))
        elif player_type == 'all-rounder':
            runs = random.randint(20, 60)
            balls = random.randint(max(15, runs), min(runs + 15, 40))
        else:  # bowler or wicket-keeper
            runs = random.randint(0, 30)
            balls = random.randint(max(5, runs), min(runs + 10, 25))
        
        fours = random.randint(0, runs // 10)
        sixes = random.randint(0, runs // 15)
        
        return runs, balls, fours, sixes
    
    def _generate_bowling_performance(self, player_type):
        """Generate bowling performance based on player type"""
        if player_type == 'bowler':
            overs = random.randint(3, 4)
            wickets = random.randint(0, 4)
            runs_conceded = random.randint(20, 40)
        elif player_type == 'all-rounder':
            overs = random.randint(2, 4)
            wickets = random.randint(0, 3)
            runs_conceded = random.randint(25, 45)
        else:  # batsman or wicket-keeper
            overs = 0
            wickets = 0
            runs_conceded = 0
        
        return overs, wickets, runs_conceded
    
    def _generate_fielding_performance(self, player_type):
        """Generate fielding performance"""
        if player_type == 'wicket-keeper':
            catches = random.randint(0, 4)
            stumpings = random.randint(0, 2)
            run_outs = random.randint(0, 1)
        else:
            catches = random.randint(0, 2)
            stumpings = 0
            run_outs = random.randint(0, 1)
        
        return catches, stumpings, run_outs
    
    def _generate_performance(self, player, match):
        """Generate performance data for a player in a match"""
        # Generate performance stats
        runs, balls, fours, sixes = self._generate_batting_performance(player.player_type)
        overs, wickets, runs_conceded = self._generate_bowling_performance(player.player_type)
        catches, stumpings, run_outs = self._generate_fielding_performance(player.player_type)
        
        # Calculate dream11 points
        points = (
            runs * 1  # 1 point per run
            + fours * 1  # 1 point per four
            + sixes * 2  # 2 points per six
            + wickets * 25  # 25 points per wicket
            + catches * 10  # 10 points per catch
            + stumpings * 15  # 15 points per stumping
            + run_outs * 10  # 10 points per run out
        )
        
        # Add bonus points
        if runs >= 50:
            points += 8  # Bonus for half-century
        if runs >= 100:
            points += 16  # Additional bonus for century
        if wickets >= 3:
            points += 8  # Bonus for 3 wickets
        if wickets >= 5:
            points += 16  # Additional bonus for 5 wickets
        
        return {
            'player_id': player.id,
            'match_id': match.id,
            'runs_scored': runs,
            'balls_faced': balls,
            'fours': fours,
            'sixes': sixes,
            'overs_bowled': overs,
            'runs_conceded': runs_conceded,
            'wickets': wickets,
            'catches': catches,
            'stumpings': stumpings,
            'run_outs': run_outs,
            'dream11_points': points,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    def populate(self):
        """Populate player performance data"""
        try:
            logger.info("Starting player performance population")
            
            # Clear existing performance data
            self.clear_table(PlayerPerformance)
            
            # Get completed matches
            completed_matches = self.session.query(Match).filter_by(status='completed').all()
            
            # Get all players
            players = self.session.query(Player).all()
            
            performances_data = []
            
            # Generate performance data for each match
            for match in completed_matches:
                # Get players from both teams
                match_players = [p for p in players if p.country in [match.team1, match.team2]]
                
                # Generate performance for each player
                for player in match_players:
                    performance_data = self._generate_performance(player, match)
                    performances_data.append(performance_data)
            
            # Create performance objects
            performances = [PlayerPerformance(**data) for data in performances_data]
            
            # Bulk insert performances
            self.bulk_insert(performances)
            
            logger.info(f"Successfully populated {len(performances)} player performances")
            return performances
        
        except Exception as e:
            logger.error(f"Error populating player performances: {str(e)}")
            raise
        finally:
            self.close_session()
