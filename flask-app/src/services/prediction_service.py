"""Services for predicting player performance and team optimization"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import random

from src.utils.constants import PlayerRoles
from .api_service import CricbuzzAPI, DataProcessor

logger = logging.getLogger(__name__)

class PerformancePredictor:
    """Predict player performance based on historical data and match conditions"""
    
    def __init__(self, api_service: CricbuzzAPI = None):
        """Initialize the PerformancePredictor
        
        Args:
            api_service: CricbuzzAPI instance
        """
        self.api_service = api_service or CricbuzzAPI()
        self.data_processor = DataProcessor(self.api_service)
        
    def predict_player_points(self, player_id: str, match_id: str, 
                              player_data: Dict = None, match_data: Dict = None) -> float:
        """Predict Dream11 points for a player in an upcoming match
        
        Args:
            player_id: Player ID
            match_id: Match ID
            player_data: Optional player data (to avoid API call)
            match_data: Optional match data (to avoid API call)
            
        Returns:
            Predicted points
        """
        try:
            # Collect data if not provided
            if not player_data:
                player_data = self.api_service.get_player_info(player_id)
            
            if not match_data:
                match_data = self.api_service.get_match_info(match_id)
            
            # Extract features for prediction
            features = self._extract_prediction_features(player_data, match_data)
            
            # Predict points using our model
            predicted_points = self._predict_with_model(features)
            
            return predicted_points
        except Exception as e:
            logger.error(f"Error predicting points for player {player_id}: {str(e)}")
            # Return a reasonable default value
            return 25.0  # Average player score
    
    def _extract_prediction_features(self, player_data: Dict, match_data: Dict) -> Dict:
        """Extract features for prediction model
        
        Args:
            player_data: Player data
            match_data: Match data
            
        Returns:
            Features for prediction
        """
        features = {}
        
        try:
            # Basic player info
            features['role'] = player_data.get('role', 'Batsman')
            
            # Recent form (last 90 days)
            form_metrics = self.data_processor.get_player_form(player_data.get('id', ''), 90)
            features['recent_form'] = form_metrics.get('overall_form', 0.5)
            features['batting_form'] = form_metrics.get('batting_form', 0.5)
            features['bowling_form'] = form_metrics.get('bowling_form', 0.5)
            
            # Batting/bowling averages
            features['batting_average'] = player_data.get('stats', {}).get('batting', {}).get('average', 25.0)
            features['bowling_average'] = player_data.get('stats', {}).get('bowling', {}).get('average', 30.0)
            
            # Venue familiarity (matches played at venue)
            venue_id = match_data.get('venue', {}).get('id', '')
            features['venue_familiarity'] = self._calculate_venue_familiarity(player_data, venue_id)
            
            # Opposition familiarity
            opposition_team = self._get_opposition_team(player_data, match_data)
            features['opposition_familiarity'] = self._calculate_opposition_familiarity(player_data, opposition_team)
            
            # Home/away advantage
            player_country = player_data.get('country', '')
            match_country = match_data.get('venue', {}).get('country', '')
            features['is_home'] = 1 if player_country == match_country else 0
            
            # Pitch conditions
            features['is_batting_pitch'] = 1 if 'batting' in match_data.get('pitch', {}).get('description', '').lower() else 0
            features['is_bowling_pitch'] = 1 if 'bowling' in match_data.get('pitch', {}).get('description', '').lower() else 0
            
            # Weather conditions
            weather = match_data.get('weather', {}).get('description', '').lower()
            features['is_sunny'] = 1 if 'sunny' in weather or 'clear' in weather else 0
            features['is_cloudy'] = 1 if 'cloud' in weather or 'overcast' in weather else 0
            features['is_rainy'] = 1 if 'rain' in weather or 'shower' in weather or 'drizzle' in weather else 0
            
            return features
        except Exception as e:
            logger.error(f"Error extracting prediction features: {str(e)}")
            # Return basic features
            return {
                'role': player_data.get('role', 'Batsman'),
                'recent_form': 0.5,
                'batting_form': 0.5,
                'bowling_form': 0.5,
                'batting_average': 25.0,
                'bowling_average': 30.0,
                'venue_familiarity': 0.5,
                'opposition_familiarity': 0.5,
                'is_home': 0,
                'is_batting_pitch': 0,
                'is_bowling_pitch': 0,
                'is_sunny': 1,
                'is_cloudy': 0,
                'is_rainy': 0
            }
    
    def _calculate_venue_familiarity(self, player_data: Dict, venue_id: str) -> float:
        """Calculate player's familiarity with venue
        
        Args:
            player_data: Player data
            venue_id: Venue ID
            
        Returns:
            Venue familiarity score (0-1)
        """
        try:
            matches_at_venue = 0
            total_matches = max(1, len(player_data.get('matches', [])))
            
            for match in player_data.get('matches', []):
                if match.get('venue', {}).get('id') == venue_id:
                    matches_at_venue += 1
            
            # Calculate familiarity (capped at 10 matches for max familiarity)
            familiarity = min(1.0, matches_at_venue / 10)
            return familiarity
        except Exception:
            return 0.5  # Default mid-range familiarity
    
    def _calculate_opposition_familiarity(self, player_data: Dict, opposition_team: str) -> float:
        """Calculate player's familiarity with opposition
        
        Args:
            player_data: Player data
            opposition_team: Opposition team name
            
        Returns:
            Opposition familiarity score (0-1)
        """
        try:
            matches_vs_opposition = 0
            total_matches = max(1, len(player_data.get('matches', [])))
            
            for match in player_data.get('matches', []):
                if opposition_team.lower() in match.get('opponent', '').lower():
                    matches_vs_opposition += 1
            
            # Calculate familiarity (capped at 10 matches for max familiarity)
            familiarity = min(1.0, matches_vs_opposition / 10)
            return familiarity
        except Exception:
            return 0.5  # Default mid-range familiarity
    
    def _get_opposition_team(self, player_data: Dict, match_data: Dict) -> str:
        """Get opposition team name for a player
        
        Args:
            player_data: Player data
            match_data: Match data
            
        Returns:
            Opposition team name
        """
        try:
            player_team = player_data.get('team', '').lower()
            team1 = match_data.get('team1', {}).get('name', '').lower()
            team2 = match_data.get('team2', {}).get('name', '').lower()
            
            if player_team in team1:
                return team2
            elif player_team in team2:
                return team1
            else:
                # If we can't determine, return the first team
                return team1
        except Exception:
            return ""
    
    def _predict_with_model(self, features: Dict) -> float:
        """Predict points using our model
        
        Args:
            features: Prediction features
            
        Returns:
            Predicted points
        """
        try:
            # This is a simplified prediction model
            # In a real implementation, this would use a trained ML model
            
            # Base points by role
            role_points = {
                'Batsman': 25.0,
                'Bowler': 25.0,
                'All-Rounder': 30.0,
                'Wicket-Keeper': 22.0
            }
            
            role = features.get('role', 'Batsman')
            base_points = role_points.get(role, 25.0)
            
            # Adjust for form (±10 points)
            form_adjustment = (features.get('recent_form', 0.5) - 0.5) * 20
            
            # Adjust for home advantage (±5 points)
            home_adjustment = 5 if features.get('is_home', 0) == 1 else 0
            
            # Adjust for pitch conditions (±5 points)
            pitch_adjustment = 0
            if role in ['Batsman', 'Wicket-Keeper'] and features.get('is_batting_pitch', 0) == 1:
                pitch_adjustment += 5
            elif role == 'Bowler' and features.get('is_bowling_pitch', 0) == 1:
                pitch_adjustment += 5
            elif role == 'All-Rounder':
                if features.get('is_batting_pitch', 0) == 1:
                    pitch_adjustment += 2.5
                if features.get('is_bowling_pitch', 0) == 1:
                    pitch_adjustment += 2.5
            
            # Adjust for weather conditions (±3 points)
            weather_adjustment = 0
            if role == 'Bowler' and features.get('is_cloudy', 0) == 1:
                weather_adjustment += 3
            elif role in ['Batsman', 'Wicket-Keeper'] and features.get('is_sunny', 0) == 1:
                weather_adjustment += 3
            
            # Adjust for familiarity (±5 points)
            familiarity_adjustment = (
                (features.get('venue_familiarity', 0.5) * 2.5) + 
                (features.get('opposition_familiarity', 0.5) * 2.5)
            ) - 2.5  # Normalize to ±2.5
            
            # Calculate total prediction
            predicted_points = base_points + form_adjustment + home_adjustment + pitch_adjustment + weather_adjustment + familiarity_adjustment
            
            # Add some randomness (±5 points)
            predicted_points += random.uniform(-5, 5)
            
            # Ensure points are positive
            predicted_points = max(0, predicted_points)
            
            return predicted_points
        except Exception as e:
            logger.error(f"Error in prediction model: {str(e)}")
            return 25.0  # Default to average points
