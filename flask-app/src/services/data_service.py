import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from src.models import Match, Player, Venue
from src.database import db

class DataService:
    """Service for fetching and processing cricket data from external APIs"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Base URLs for different cricket APIs (you'll need to replace these with actual API endpoints)
        self.cricket_api_base_url = "https://api.cricket-data.org/v1"
        self.weather_api_base_url = "https://api.weatherapi.com/v1"
    
    def fetch_upcoming_matches(self, days: int = 7) -> List[Dict]:
        """Fetch upcoming cricket matches"""
        try:
            # Calculate date range
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Make API request
            endpoint = f"{self.cricket_api_base_url}/matches"
            params = {
                "dateFrom": start_date,
                "dateTo": end_date,
                "apikey": self.api_key
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            matches_data = response.json()
            
            # Process and store matches
            processed_matches = []
            for match_data in matches_data:
                match = self._process_match_data(match_data)
                if match:
                    processed_matches.append(match)
            
            return processed_matches
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching upcoming matches: {str(e)}")
            return []
    
    def fetch_player_stats(self, player_id: int) -> Dict:
        """Fetch detailed player statistics"""
        try:
            endpoint = f"{self.cricket_api_base_url}/players/{player_id}"
            params = {"apikey": self.api_key}
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            player_data = response.json()
            return self._process_player_stats(player_data)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching player stats: {str(e)}")
            return {}
    
    def fetch_venue_stats(self, venue_id: int) -> Dict:
        """Fetch venue statistics and characteristics"""
        try:
            endpoint = f"{self.cricket_api_base_url}/venues/{venue_id}"
            params = {"apikey": self.api_key}
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            venue_data = response.json()
            return self._process_venue_data(venue_data)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching venue stats: {str(e)}")
            return {}
    
    def fetch_weather_forecast(self, venue: Venue, match_date: datetime) -> Dict:
        """Fetch weather forecast for match venue"""
        try:
            endpoint = f"{self.weather_api_base_url}/forecast.json"
            params = {
                "key": self.api_key,
                "q": f"{venue.latitude},{venue.longitude}",
                "dt": match_date.strftime("%Y-%m-%d")
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            weather_data = response.json()
            return self._process_weather_data(weather_data)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching weather forecast: {str(e)}")
            return {}
    
    def fetch_historical_performances(self, player_id: int, num_matches: int = 10) -> List[Dict]:
        """Fetch player's historical performances"""
        try:
            endpoint = f"{self.cricket_api_base_url}/players/{player_id}/matches"
            params = {
                "apikey": self.api_key,
                "limit": num_matches
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            performances = response.json()
            return [self._process_performance_data(perf) for perf in performances]
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching historical performances: {str(e)}")
            return []
    
    def fetch_matches_via_perplexity(self, days: int = 7) -> List[Dict]:
        """Fetch upcoming cricket matches using Perplexity API"""
        try:
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {"role": "system", "content": "Be precise and concise."},
                    {"role": "user", "content": f"List upcoming cricket matches for the next {days} days."}
                ]
            }
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [])[0].get("message", {}).get("content", "")
            # TODO: parse 'content' string into structured match dicts
            return content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching matches via Perplexity: {e}")
            return []

    def _process_match_data(self, match_data: Dict) -> Optional[Match]:
        """Process raw match data and create/update Match object"""
        try:
            match = Match(
                external_id=match_data.get('id'),
                team1=match_data.get('team1'),
                team2=match_data.get('team2'),
                venue_id=match_data.get('venue_id'),
                start_time=datetime.fromisoformat(match_data.get('startTime')),
                match_type=match_data.get('matchType'),
                status=match_data.get('status')
            )
            
            db.session.add(match)
            db.session.commit()
            
            return match
            
        except Exception as e:
            self.logger.error(f"Error processing match data: {str(e)}")
            db.session.rollback()
            return None
    
    def _process_player_stats(self, player_data: Dict) -> Dict:
        """Process raw player statistics"""
        try:
            return {
                'batting_avg': float(player_data.get('batting_average', 0)),
                'bowling_avg': float(player_data.get('bowling_average', 0)),
                'recent_form': self._calculate_recent_form(player_data.get('recent_matches', [])),
                'player_type': player_data.get('player_type'),
                'total_matches': int(player_data.get('matches_played', 0)),
                'strike_rate': float(player_data.get('strike_rate', 0)),
                'economy_rate': float(player_data.get('economy_rate', 0))
            }
        except Exception as e:
            self.logger.error(f"Error processing player stats: {str(e)}")
            return {}
    
    def _process_venue_data(self, venue_data: Dict) -> Dict:
        """Process raw venue data"""
        try:
            return {
                'name': venue_data.get('name'),
                'location': venue_data.get('location'),
                'capacity': int(venue_data.get('capacity', 0)),
                'pitch_type': venue_data.get('pitch_type'),
                'boundary_lengths': venue_data.get('boundary_lengths', {}),
                'average_first_innings_score': float(venue_data.get('avg_first_innings_score', 0)),
                'average_second_innings_score': float(venue_data.get('avg_second_innings_score', 0))
            }
        except Exception as e:
            self.logger.error(f"Error processing venue data: {str(e)}")
            return {}
    
    def _process_weather_data(self, weather_data: Dict) -> Dict:
        """Process raw weather forecast data"""
        try:
            return {
                'temperature': float(weather_data.get('temp_c', 0)),
                'humidity': float(weather_data.get('humidity', 0)),
                'wind_speed': float(weather_data.get('wind_kph', 0)),
                'precipitation_chance': float(weather_data.get('precip_mm', 0)),
                'condition': weather_data.get('condition', {}).get('text', '')
            }
        except Exception as e:
            self.logger.error(f"Error processing weather data: {str(e)}")
            return {}
    
    def _process_performance_data(self, performance_data: Dict) -> Dict:
        """Process raw performance data"""
        try:
            return {
                'runs_scored': int(performance_data.get('runs', 0)),
                'balls_faced': int(performance_data.get('balls', 0)),
                'wickets_taken': int(performance_data.get('wickets', 0)),
                'overs_bowled': float(performance_data.get('overs', 0)),
                'runs_conceded': int(performance_data.get('runs_conceded', 0)),
                'catches': int(performance_data.get('catches', 0)),
                'stumpings': int(performance_data.get('stumpings', 0)),
                'dream11_points': self._calculate_dream11_points(performance_data)
            }
        except Exception as e:
            self.logger.error(f"Error processing performance data: {str(e)}")
            return {}
    
    def _calculate_dream11_points(self, performance_data: Dict) -> float:
        """Calculate Dream11 points from performance data"""
        points = 0
        
        # Batting points
        runs = int(performance_data.get('runs', 0))
        points += runs  # 1 point per run
        if runs >= 50:
            points += 8  # Bonus for half-century
        if runs >= 100:
            points += 16  # Additional bonus for century
            
        # Bowling points
        wickets = int(performance_data.get('wickets', 0))
        points += wickets * 25  # 25 points per wicket
        if wickets >= 3:
            points += 8  # Bonus for 3-wicket haul
        if wickets >= 5:
            points += 16  # Additional bonus for 5-wicket haul
            
        # Fielding points
        points += int(performance_data.get('catches', 0)) * 8  # 8 points per catch
        points += int(performance_data.get('stumpings', 0)) * 12  # 12 points per stumping
        
        # Economy rate bonus/penalty (for bowlers)
        overs = float(performance_data.get('overs', 0))
        if overs >= 2:
            economy = float(performance_data.get('runs_conceded', 0)) / overs
            if economy < 4:
                points += 6
            elif economy < 5:
                points += 4
            elif economy < 6:
                points += 2
            elif economy > 9:
                points -= 2
            elif economy > 10:
                points -= 4
            elif economy > 11:
                points -= 6
        
        return points
    
    def _calculate_recent_form(self, recent_matches: List[Dict]) -> float:
        """Calculate player's recent form based on Dream11 points"""
        if not recent_matches:
            return 0
            
        total_points = sum(self._calculate_dream11_points(match) for match in recent_matches)
        return total_points / len(recent_matches)
    
    def update_player_database(self):
        """Update player database with latest information"""
        try:
            players = Player.query.all()
            for player in players:
                stats = self.fetch_player_stats(player.external_id)
                if stats:
                    player.batting_average = stats.get('batting_avg')
                    player.bowling_average = stats.get('bowling_avg')
                    player.recent_form = stats.get('recent_form')
                    player.total_matches = stats.get('total_matches')
                    player.strike_rate = stats.get('strike_rate')
                    player.economy_rate = stats.get('economy_rate')
                    
            db.session.commit()
            self.logger.info("Player database updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating player database: {str(e)}")
            db.session.rollback()
    
    def update_match_status(self, match_id: int):
        """Update match status and related information"""
        try:
            match = Match.query.get(match_id)
            if not match:
                return
                
            # Fetch latest match data
            endpoint = f"{self.cricket_api_base_url}/matches/{match.external_id}"
            params = {"apikey": self.api_key}
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            match_data = response.json()
            
            # Update match status
            match.status = match_data.get('status')
            match.result = match_data.get('result')
            match.winner = match_data.get('winner')
            
            # Update player performances if match is completed
            if match.status == 'completed':
                self._update_match_performances(match, match_data)
            
            db.session.commit()
            self.logger.info(f"Match {match_id} status updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating match status: {str(e)}")
            db.session.rollback()
    
    def _update_match_performances(self, match: Match, match_data: Dict):
        """Update player performances for a completed match"""
        try:
            performances = match_data.get('performances', [])
            for perf_data in performances:
                player_id = perf_data.get('player_id')
                if not player_id:
                    continue
                    
                performance = MatchPerformance(
                    match_id=match.id,
                    player_id=player_id,
                    runs_scored=perf_data.get('runs', 0),
                    balls_faced=perf_data.get('balls', 0),
                    wickets_taken=perf_data.get('wickets', 0),
                    overs_bowled=perf_data.get('overs', 0),
                    runs_conceded=perf_data.get('runs_conceded', 0),
                    catches=perf_data.get('catches', 0),
                    stumpings=perf_data.get('stumpings', 0),
                    dream11_points=self._calculate_dream11_points(perf_data)
                )
                
                db.session.add(performance)
            
            db.session.commit()
            self.logger.info(f"Match performances updated for match {match.id}")
            
        except Exception as e:
            self.logger.error(f"Error updating match performances: {str(e)}")
            db.session.rollback()
