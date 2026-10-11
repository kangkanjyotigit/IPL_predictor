"""Services for integrating with external APIs and data sources"""

import http.client
import json
import os
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

class CricbuzzAPI:
    """Service for interacting with the Cricbuzz API"""
    
    BASE_URL = "cricbuzz-cricket.p.rapidapi.com"
    CACHE_DURATION = 300  # 5 minutes cache
    
    def __init__(self, api_key=None):
        """Initialize the CricbuzzAPI service
        
        Args:
            api_key: API key for RapidAPI. If None, will look for CRICBUZZ_API_KEY env var.
        """
        # Use the provided API key from RapidAPI
        self.api_key = api_key or os.environ.get("CRICBUZZ_API_KEY", os.environ["RAPIDAPI_KEY"])
        
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': self.BASE_URL
        }
        self._cache = {}
        
        # Test the API key on initialization
        try:
            # Make a simple API call to test the key
            self._test_api_connection()
            logger.info("API connection successfully established")
        except Exception as e:
            logger.warning(f"API connection test failed: {str(e)}. Will use mock data instead.")
        
    def _get_from_cache(self, endpoint: str) -> Optional[Dict]:
        """Get data from cache if it exists and is not expired
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Cached data or None if not in cache or expired
        """
        if endpoint in self._cache:
            data, timestamp = self._cache[endpoint]
            if time.time() - timestamp < self.CACHE_DURATION:
                logger.debug(f"Returning cached data for {endpoint}")
                return data
        return None
    
    def _add_to_cache(self, endpoint: str, data: Dict) -> None:
        """Add data to cache
        
        Args:
            endpoint: API endpoint
            data: Data to cache
        """
        self._cache[endpoint] = (data, time.time())
    
    def _make_request(self, endpoint: str, force_refresh=False) -> Dict:
        """Make a request to the Cricbuzz API
        
        Args:
            endpoint: API endpoint
            force_refresh: Force refresh even if cached data exists
            
        Returns:
            JSON response as dict
        """
        if not force_refresh:
            cached_data = self._get_from_cache(endpoint)
            if cached_data:
                return cached_data
        
        # First check if we should use mock data
        if '/matches/v1/' in endpoint:
            # Extract match type from endpoint
            match_type = endpoint.split('/')[-1]
            try:
                # Try to make the actual API request
                conn = http.client.HTTPSConnection(self.BASE_URL)
                logger.info(f"Making request to {endpoint}")
                conn.request("GET", endpoint, headers=self.headers)
                res = conn.getresponse()
                data = res.read()
                
                # Check if we got a valid response
                if res.status == 200:
                    response = json.loads(data.decode("utf-8"))
                    
                    # If response is empty or has no matches, use mock data
                    if not response or 'typeMatches' not in response or not response['typeMatches']:
                        logger.warning(f"Empty response from API for {endpoint}, using mock data")
                        response = self.get_mock_matches(match_type)
                else:
                    logger.warning(f"API request failed with status {res.status}, using mock data")
                    response = self.get_mock_matches(match_type)
                
                # Cache the response
                self._add_to_cache(endpoint, response)
                return response
            except Exception as e:
                logger.error(f"Error making request to {endpoint}: {str(e)}")
                logger.info("Using mock data instead")
                response = self.get_mock_matches(match_type)
                self._add_to_cache(endpoint, response)
                return response
            finally:
                try:
                    conn.close()
                except:
                    pass
        else:
            # For other API endpoints
            conn = http.client.HTTPSConnection(self.BASE_URL)
            try:
                logger.info(f"Making request to {endpoint}")
                conn.request("GET", endpoint, headers=self.headers)
                res = conn.getresponse()
                data = res.read()
                
                if res.status == 200:
                    response = json.loads(data.decode("utf-8"))
                    # Cache the response
                    self._add_to_cache(endpoint, response)
                    return response
                else:
                    logger.error(f"API request failed with status {res.status}")
                    # Return empty dict for non-match endpoints
                    return {}
            except Exception as e:
                logger.error(f"Error making request to {endpoint}: {str(e)}")
                return {}
            finally:
                conn.close()
    
    def get_match_info(self, match_id: str) -> Dict:
        """Get detailed information about a match
        
        Args:
            match_id: Cricbuzz match ID
            
        Returns:
            Match information
        """
        endpoint = f"/mcenter/v1/{match_id}/info"
        return self._make_request(endpoint)
    
    def get_match_commentary(self, match_id: str) -> Dict:
        """Get live commentary for a match
        
        Args:
            match_id: Cricbuzz match ID
            
        Returns:
            Match commentary
        """
        endpoint = f"/mcenter/v1/{match_id}/comm"
        return self._make_request(endpoint)
    
    def get_match_scorecard(self, match_id: str) -> Dict:
        """Get scorecard for a match
        
        Args:
            match_id: Cricbuzz match ID
            
        Returns:
            Match scorecard
        """
        endpoint = f"/mcenter/v1/{match_id}/scard"
        return self._make_request(endpoint)
    
    def get_player_info(self, player_id: str) -> Dict:
        """Get detailed information about a player
        
        Args:
            player_id: Cricbuzz player ID
            
        Returns:
            Player information
        """
        endpoint = f"/stats/v1/player/{player_id}"
        return self._make_request(endpoint)
    
    def get_matches_list(self, match_type: str = "all") -> Dict:
        """Get list of matches
        
        Args:
            match_type: Type of matches (all, live, upcoming, recent)
            
        Returns:
            List of matches
        """
        endpoint = f"/matches/v1/{match_type}"
        return self._make_request(endpoint)
    
    def get_series_list(self) -> Dict:
        """Get list of cricket series
        
        Returns:
            List of series
        """
        endpoint = "/series/v1/international"
        return self._make_request(endpoint)
        
    def _test_api_connection(self):
        """Test the API connection with a simple request
        
        Raises an exception if the connection fails
        """
        test_endpoint = "/matches/v1/live"  # Use a simple endpoint for testing
        conn = http.client.HTTPSConnection(self.BASE_URL)
        try:
            conn.request("GET", test_endpoint, headers=self.headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status != 200:
                raise Exception(f"API test failed with status code {res.status}: {data.decode('utf-8')}")
                
            # Try to parse the response to verify it's valid JSON
            json.loads(data.decode("utf-8"))
        finally:
            conn.close()
            
    def get_mock_matches(self, match_type="upcoming"):
        """Get mock matches data for testing when API is unavailable
        
        Args:
            match_type: Type of matches (upcoming, live, recent)
            
        Returns:
            Mock match data
        """
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        
        # Create some mock IPL matches
        mock_matches = {
            "typeMatches": [
                {
                    "matchType": "T20",
                    "seriesMatches": [
                        {
                            "seriesAdWrapper": {
                                "seriesName": "Indian Premier League 2025",
                                "matches": [
                                    {
                                        "matchInfo": {
                                            "id": "102501",
                                            "team1": {
                                                "id": "141",
                                                "name": "Mumbai Indians",
                                                "shortName": "MI"
                                            },
                                            "team2": {
                                                "id": "142",
                                                "name": "Chennai Super Kings",
                                                "shortName": "CSK"
                                            },
                                            "matchFormat": "T20",
                                            "startDate": str(int(today.timestamp() * 1000)),
                                            "endDate": str(int((today + timedelta(hours=4)).timestamp() * 1000)),
                                            "state": "In Progress",
                                            "status": "Chennai Super Kings opt to bowl",
                                            "venue": {
                                                "id": "170",
                                                "name": "Wankhede Stadium"
                                            }
                                        }
                                    },
                                    {
                                        "matchInfo": {
                                            "id": "102502",
                                            "team1": {
                                                "id": "143",
                                                "name": "Royal Challengers Bangalore",
                                                "shortName": "RCB"
                                            },
                                            "team2": {
                                                "id": "144",
                                                "name": "Kolkata Knight Riders",
                                                "shortName": "KKR"
                                            },
                                            "matchFormat": "T20",
                                            "startDate": str(int(tomorrow.timestamp() * 1000)),
                                            "endDate": str(int((tomorrow + timedelta(hours=4)).timestamp() * 1000)),
                                            "state": "Upcoming",
                                            "status": "Match starts at 19:30 IST",
                                            "venue": {
                                                "id": "171",
                                                "name": "M. Chinnaswamy Stadium"
                                            }
                                        }
                                    },
                                    {
                                        "matchInfo": {
                                            "id": "102503",
                                            "team1": {
                                                "id": "145",
                                                "name": "Delhi Capitals",
                                                "shortName": "DC"
                                            },
                                            "team2": {
                                                "id": "146",
                                                "name": "Rajasthan Royals",
                                                "shortName": "RR"
                                            },
                                            "matchFormat": "T20",
                                            "startDate": str(int(yesterday.timestamp() * 1000)),
                                            "endDate": str(int((yesterday + timedelta(hours=4)).timestamp() * 1000)),
                                            "state": "Complete",
                                            "status": "Rajasthan Royals won by 6 wickets",
                                            "venue": {
                                                "id": "172",
                                                "name": "Arun Jaitley Stadium"
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        
        return mock_matches
    
    def get_series_matches(self, series_id: str) -> Dict:
        """Get matches for a series
        
        Args:
            series_id: Cricbuzz series ID
            
        Returns:
            Series matches
        """
        endpoint = f"/series/v1/{series_id}/matches"
        return self._make_request(endpoint)
        
    def get_ipl_matches(self, series_id: str = None) -> Dict:
        """Get current IPL matches
        
        Args:
            series_id: Optional specific IPL series ID. If None, will try to find
                      the latest IPL series automatically.
            
        Returns:
            IPL matches information
        """
        if not series_id:
            # Try to find the latest IPL series
            series_list = self.get_series_list()
            for series_type in series_list.get('seriesTypes', []):
                for series in series_type.get('series', []):
                    if 'IPL' in series.get('name', '').upper() or 'INDIAN PREMIER LEAGUE' in series.get('name', '').upper():
                        # Found IPL series
                        series_id = series.get('id')
                        logger.info(f"Found IPL series: {series.get('name')} with ID {series_id}")
                        break
                if series_id:
                    break
        
        if not series_id:
            logger.warning("Could not find any active IPL series")
            return {"matches": []}
            
        # Get matches for the IPL series
        return self.get_series_matches(series_id)
    
    def fetch_player_statistics(self, player_id: str) -> Dict:
        """Fetch detailed statistics for a player
        
        Args:
            player_id: Cricbuzz player ID
            
        Returns:
            Player statistics
        """
        endpoint = f"/stats/v1/player/details/{player_id}"
        return self._make_request(endpoint)


class DataProcessor:
    """Process data from APIs into formats usable by our models"""
    
    def __init__(self, api_service: CricbuzzAPI):
        """Initialize the DataProcessor
        
        Args:
            api_service: API service instance
        """
        self.api_service = api_service
        
    def process_match_data(self, match_id: str) -> Dict:
        """Process match data to extract relevant information
        
        Args:
            match_id: Cricbuzz match ID
            
        Returns:
            Processed match data
        """
        try:
            # Get match info and scorecard
            match_info = self.api_service.get_match_info(match_id)
            scorecard = self.api_service.get_match_scorecard(match_id)
            
            # Extract relevant data
            processed_data = {
                'match_id': match_id,
                'teams': {
                    'team1': self._extract_team_data(match_info, 'team1'),
                    'team2': self._extract_team_data(match_info, 'team2')
                },
                'venue': self._extract_venue_data(match_info),
                'players': self._extract_player_data(match_info, scorecard),
                'weather': self._extract_weather_data(match_info),
                'toss': self._extract_toss_data(match_info)
            }
            
            return processed_data
        except Exception as e:
            logger.error(f"Error processing match data for {match_id}: {str(e)}")
            raise
    
    def _extract_team_data(self, match_info: Dict, team_key: str) -> Dict:
        """Extract team data from match info
        
        Args:
            match_info: Match information
            team_key: Team key (team1 or team2)
            
        Returns:
            Team data
        """
        try:
            team_data = match_info.get('matchHeader', {}).get('team1' if team_key == 'team1' else 'team2', {})
            return {
                'id': team_data.get('id'),
                'name': team_data.get('name'),
                'short_name': team_data.get('shortName'),
                'logo_url': team_data.get('logoUrl')
            }
        except Exception:
            # Return empty dict if data not available
            return {}
    
    def _extract_venue_data(self, match_info: Dict) -> Dict:
        """Extract venue data from match info
        
        Args:
            match_info: Match information
            
        Returns:
            Venue data
        """
        try:
            venue_data = match_info.get('matchHeader', {}).get('venue', {})
            return {
                'id': venue_data.get('id'),
                'name': venue_data.get('name'),
                'location': venue_data.get('location'),
                'country': venue_data.get('country')
            }
        except Exception:
            # Return empty dict if data not available
            return {}
    
    def _extract_player_data(self, match_info: Dict, scorecard: Dict) -> List[Dict]:
        """Extract player data from match info and scorecard
        
        Args:
            match_info: Match information
            scorecard: Match scorecard
            
        Returns:
            List of player data
        """
        players = []
        try:
            # Extract players from teams
            team1_players = match_info.get('matchHeader', {}).get('team1', {}).get('players', [])
            team2_players = match_info.get('matchHeader', {}).get('team2', {}).get('players', [])
            
            # Extract team names for reference
            team1_name = match_info.get('matchHeader', {}).get('team1', {}).get('name')
            team2_name = match_info.get('matchHeader', {}).get('team2', {}).get('name')
            
            # Process team 1 players
            for player in team1_players:
                player_data = {
                    'id': player.get('id'),
                    'name': player.get('name'),
                    'role': player.get('role'),
                    'team_name': team1_name,
                    'batting_stats': self._extract_batting_stats(scorecard, player.get('id')),
                    'bowling_stats': self._extract_bowling_stats(scorecard, player.get('id')),
                }
                players.append(player_data)
            
            # Process team 2 players
            for player in team2_players:
                player_data = {
                    'id': player.get('id'),
                    'name': player.get('name'),
                    'role': player.get('role'),
                    'team_name': team2_name,
                    'batting_stats': self._extract_batting_stats(scorecard, player.get('id')),
                    'bowling_stats': self._extract_bowling_stats(scorecard, player.get('id')),
                }
                players.append(player_data)
            
            return players
        except Exception:
            # Return empty list if data not available
            return players
    
    def _extract_batting_stats(self, scorecard: Dict, player_id: str) -> Dict:
        """Extract batting statistics for a player from scorecard
        
        Args:
            scorecard: Match scorecard
            player_id: Player ID
            
        Returns:
            Batting statistics
        """
        try:
            # Initialize with default values
            batting_stats = {
                'runs': 0,
                'balls': 0,
                'fours': 0,
                'sixes': 0,
                'strike_rate': 0.0,
                'is_out': False,
                'dismissal': None
            }
            
            # Look through scorecard innings
            for innings in scorecard.get('scorecard', []):
                for batsman in innings.get('batsmen', []):
                    if str(batsman.get('id')) == str(player_id):
                        batting_stats.update({
                            'runs': batsman.get('runs', 0),
                            'balls': batsman.get('balls', 0),
                            'fours': batsman.get('fours', 0),
                            'sixes': batsman.get('sixes', 0),
                            'strike_rate': batsman.get('strikerate', 0.0),
                            'is_out': batsman.get('isOut', False),
                            'dismissal': batsman.get('dismissal')
                        })
                        break
            
            return batting_stats
        except Exception:
            # Return default values if data not available
            return {
                'runs': 0,
                'balls': 0,
                'fours': 0,
                'sixes': 0,
                'strike_rate': 0.0,
                'is_out': False,
                'dismissal': None
            }
    
    def _extract_bowling_stats(self, scorecard: Dict, player_id: str) -> Dict:
        """Extract bowling statistics for a player from scorecard
        
        Args:
            scorecard: Match scorecard
            player_id: Player ID
            
        Returns:
            Bowling statistics
        """
        try:
            # Initialize with default values
            bowling_stats = {
                'overs': 0,
                'maidens': 0,
                'runs': 0,
                'wickets': 0,
                'economy': 0.0,
                'extras': 0
            }
            
            # Look through scorecard innings
            for innings in scorecard.get('scorecard', []):
                for bowler in innings.get('bowlers', []):
                    if str(bowler.get('id')) == str(player_id):
                        bowling_stats.update({
                            'overs': bowler.get('overs', 0),
                            'maidens': bowler.get('maidens', 0),
                            'runs': bowler.get('runs', 0),
                            'wickets': bowler.get('wickets', 0),
                            'economy': bowler.get('economy', 0.0),
                            'extras': bowler.get('extras', 0)
                        })
                        break
            
            return bowling_stats
        except Exception:
            # Return default values if data not available
            return {
                'overs': 0,
                'maidens': 0,
                'runs': 0,
                'wickets': 0,
                'economy': 0.0,
                'extras': 0
            }
    
    def _extract_weather_data(self, match_info: Dict) -> Dict:
        """Extract weather data from match info
        
        Args:
            match_info: Match information
            
        Returns:
            Weather data
        """
        try:
            weather_data = match_info.get('matchHeader', {}).get('weatherInfo', {})
            return {
                'description': weather_data.get('description'),
                'temperature': weather_data.get('temperature'),
                'humidity': weather_data.get('humidity'),
                'wind': weather_data.get('wind')
            }
        except Exception:
            # Return empty dict if data not available
            return {}
    
    def _extract_toss_data(self, match_info: Dict) -> Dict:
        """Extract toss data from match info
        
        Args:
            match_info: Match information
            
        Returns:
            Toss data
        """
        try:
            toss_data = match_info.get('matchHeader', {}).get('toss', {})
            return {
                'winner': toss_data.get('winner'),
                'decision': toss_data.get('decision')
            }
        except Exception:
            # Return empty dict if data not available
            return {}
    
    def get_player_form(self, player_id: str, timeframe_days: int = 90) -> Dict:
        """Calculate player form based on recent performances
        
        Args:
            player_id: Player ID
            timeframe_days: Number of days to consider for recent form
            
        Returns:
            Player form metrics
        """
        try:
            # Get player statistics
            player_stats = self.api_service.fetch_player_statistics(player_id)
            
            # Calculate recent form
            recent_form = self._calculate_recent_form(player_stats, timeframe_days)
            
            return recent_form
        except Exception as e:
            logger.error(f"Error getting player form for {player_id}: {str(e)}")
            return {
                'batting_form': 0.5,  # Default mid-range form
                'bowling_form': 0.5,
                'overall_form': 0.5
            }
    
    def _calculate_recent_form(self, player_stats: Dict, timeframe_days: int) -> Dict:
        """Calculate recent form based on player statistics
        
        Args:
            player_stats: Player statistics
            timeframe_days: Number of days to consider for recent form
            
        Returns:
            Recent form metrics
        """
        # Initialize form metrics
        form_metrics = {
            'batting_form': 0.5,
            'bowling_form': 0.5,
            'overall_form': 0.5
        }
        
        try:
            # Get recent matches within timeframe
            cutoff_date = datetime.now() - timedelta(days=timeframe_days)
            recent_matches = []
            
            # Filter recent matches
            for match in player_stats.get('matches', []):
                match_date = datetime.strptime(match.get('date', '1970-01-01'), '%Y-%m-%d')
                if match_date >= cutoff_date:
                    recent_matches.append(match)
            
            if not recent_matches:
                return form_metrics
            
            # Calculate batting form
            batting_points = 0
            batting_matches = 0
            for match in recent_matches:
                if 'batting' in match:
                    batting_matches += 1
                    # Calculate points based on runs, SR, etc.
                    runs = match.get('batting', {}).get('runs', 0)
                    strike_rate = match.get('batting', {}).get('strikerate', 0)
                    
                    # Award points for runs (0.1 points per run)
                    batting_points += runs * 0.1
                    
                    # Award points for strike rate
                    if strike_rate > 150:
                        batting_points += 5
                    elif strike_rate > 120:
                        batting_points += 3
                    elif strike_rate > 100:
                        batting_points += 1
            
            # Calculate bowling form
            bowling_points = 0
            bowling_matches = 0
            for match in recent_matches:
                if 'bowling' in match:
                    bowling_matches += 1
                    # Calculate points based on wickets, economy, etc.
                    wickets = match.get('bowling', {}).get('wickets', 0)
                    economy = match.get('bowling', {}).get('economy', 10)
                    
                    # Award points for wickets (10 points per wicket)
                    bowling_points += wickets * 10
                    
                    # Award points for economy
                    if economy < 6:
                        bowling_points += 5
                    elif economy < 8:
                        bowling_points += 3
                    elif economy < 10:
                        bowling_points += 1
            
            # Normalize form scores (0-1 range)
            if batting_matches > 0:
                batting_form = min(1.0, batting_points / (batting_matches * 50))  # 50 points is a good innings
                form_metrics['batting_form'] = batting_form
            
            if bowling_matches > 0:
                bowling_form = min(1.0, bowling_points / (bowling_matches * 30))  # 30 points is a good bowling spell
                form_metrics['bowling_form'] = bowling_form
            
            # Calculate overall form (weighted average)
            if batting_matches > 0 or bowling_matches > 0:
                form_metrics['overall_form'] = (
                    (form_metrics['batting_form'] * batting_matches) + 
                    (form_metrics['bowling_form'] * bowling_matches)
                ) / max(1, (batting_matches + bowling_matches))
            
            return form_metrics
        
        except Exception as e:
            logger.error(f"Error calculating recent form: {str(e)}")
            return form_metrics


class MatchImporter:
    """Import matches and player data from Cricbuzz API into our database"""
    
    def __init__(self, api_service, db, Player, Match, Venue):
        """Initialize the MatchImporter
        
        Args:
            api_service: API service instance
            db: Database instance
            Player: Player model class
            Match: Match model class
            Venue: Venue model class
        """
        self.api_service = api_service
        self.db = db
        self.Player = Player
        self.Match = Match
        self.Venue = Venue
        self.data_processor = DataProcessor(api_service)
    
    def import_upcoming_matches(self):
        """Import upcoming matches from Cricbuzz API"""
        try:
            # Get upcoming matches
            matches_list = self.api_service.get_matches_list("upcoming")
            
            # Get recent matches too for more options
            recent_matches_list = self.api_service.get_matches_list("recent")
            
            matches_imported = 0
            
            # Process upcoming matches
            for match_type in matches_list.get('typeMatches', []):
                for series in match_type.get('seriesMatches', []):
                    series_name = series.get('seriesAdWrapper', {}).get('seriesName', 'Unknown Series')
                    logger.info(f"Processing upcoming matches from series: {series_name}")
                    
                    for match_data in series.get('seriesAdWrapper', {}).get('matches', []):
                        match = match_data.get('matchInfo', {})
                        match_id = match.get('id')
                        match_format = match.get('matchFormat')
                        
                        if not match_id:
                            continue
                            
                        # Import match details for all formats now
                        logger.info(f"Importing {match_format} match {match_id} from {series_name}")
                        self._import_match(match_id)
                        matches_imported += 1
            
            # Process recent matches (last 7 days) for ongoing tournaments
            recent_count = 0
            for match_type in recent_matches_list.get('typeMatches', []):
                for series in match_type.get('seriesMatches', []):
                    # Only import a reasonable number of recent matches
                    if recent_count >= 10:  # Limit to avoid too many old matches
                        break
                        
                    series_name = series.get('seriesAdWrapper', {}).get('seriesName', 'Unknown Series')
                    
                    for match_data in series.get('seriesAdWrapper', {}).get('matches', []):
                        match = match_data.get('matchInfo', {})
                        match_id = match.get('id')
                        
                        if not match_id:
                            continue
                            
                        # Check if this match is recent (within last 2 days)
                        match_date = match.get('startDate')
                        if match_date and self._is_match_recent(match_date):
                            self._import_match(match_id)
                            matches_imported += 1
                            recent_count += 1
                            
                        # Limit to 10 recent matches total
                        if recent_count >= 10:
                            break
            
            logger.info(f"Imported {matches_imported} cricket matches in total")
            return matches_imported
        except Exception as e:
            logger.error(f"Error importing upcoming matches: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
            
    def _is_match_recent(self, match_date_str):
        """Check if a match is recent (within last 2 days)
        
        Args:
            match_date_str: Match date string from API
            
        Returns:
            True if match is recent, False otherwise
        """
        try:
            from datetime import datetime, timedelta
            
            # Convert match date string to datetime
            match_date = datetime.fromtimestamp(int(match_date_str)/1000)
            
            # Check if match is within last 2 days
            two_days_ago = datetime.now() - timedelta(days=2)
            return match_date >= two_days_ago
        except Exception as e:
            logger.error(f"Error parsing match date: {str(e)}")
            return False
            
    def import_ipl_matches(self, series_id=None):
        """Import IPL matches from Cricbuzz API
        
        Args:
            series_id: Optional specific IPL series ID. If None, will try to find
                      the latest IPL series automatically.
        
        Returns:
            Number of matches imported
        """
        try:
            # Get IPL matches
            ipl_data = self.api_service.get_ipl_matches(series_id)
            
            matches_imported = 0
            if 'matchDetails' in ipl_data:
                # Process matches in the series
                for match_detail in ipl_data.get('matchDetails', []):
                    match = match_detail.get('matchInfo', {})
                    match_id = match.get('id')
                    
                    if not match_id:
                        continue
                        
                    # Only import matches that haven't happened yet or are ongoing
                    match_status = match.get('state')
                    if match_status in ['Complete', 'Abandoned']:
                        logger.debug(f"Skipping already completed match {match_id}")
                        continue
                    
                    # Import match details
                    self._import_match(match_id)
                    matches_imported += 1
            else:
                # Alternative structure sometimes returned by the API
                for match_data in ipl_data.get('matches', []):
                    match = match_data.get('matchInfo', {})
                    match_id = match.get('id')
                    
                    if not match_id:
                        continue
                        
                    # Only import matches that haven't happened yet or are ongoing
                    match_status = match.get('state')
                    if match_status in ['Complete', 'Abandoned']:
                        logger.debug(f"Skipping already completed match {match_id}")
                        continue
                    
                    # Import match details
                    self._import_match(match_id)
                    matches_imported += 1
            
            logger.info(f"Imported {matches_imported} IPL matches")
            return matches_imported
        except Exception as e:
            logger.error(f"Error importing IPL matches: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def _import_match(self, match_id):
        """Import a single match and related data
        
        Args:
            match_id: Cricbuzz match ID
        """
        try:
            # Get detailed match data
            match_data = self.data_processor.process_match_data(match_id)
            
            # Check if match already exists
            existing_match = self.Match.query.filter_by(external_id=match_id).first()
            if existing_match:
                logger.info(f"Match {match_id} already exists, updating")
                # Update match details
                self._update_match(existing_match, match_data)
            else:
                logger.info(f"Importing new match {match_id}")
                # Create venue if needed
                venue = self._get_or_create_venue(match_data['venue'])
                
                # Create new match
                new_match = self.Match(
                    external_id=match_id,
                    team1=match_data['teams']['team1'].get('name'),
                    team2=match_data['teams']['team2'].get('name'),
                    format=match_data.get('format', 'T20'),
                    series_name=match_data.get('series_name'),
                    venue_id=venue.id if venue else None,
                    date=datetime.strptime(match_data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d'),
                    status='upcoming'
                )
                self.db.session.add(new_match)
                self.db.session.flush()  # Get the ID without committing
                
                # Import players
                self._import_players(match_data['players'])
            
            self.db.session.commit()
            
        except Exception as e:
            logger.error(f"Error importing match {match_id}: {str(e)}")
            self.db.session.rollback()
            raise
    
    def _update_match(self, match, match_data):
        """Update an existing match with new data
        
        Args:
            match: Match object
            match_data: New match data
        """
        # Update venue if needed
        venue = self._get_or_create_venue(match_data['venue'])
        if venue:
            match.venue_id = venue.id
            match.venue = venue.name
        
        # Update other fields as needed
        match.date = datetime.strptime(match_data.get('date', match.date.strftime('%Y-%m-%d')), '%Y-%m-%d')
        match.status = match_data.get('status', match.status)
        
        # Import/update players
        self._import_players(match_data['players'])
    
    def _get_or_create_venue(self, venue_data):
        """Get existing venue or create a new one
        
        Args:
            venue_data: Venue data
            
        Returns:
            Venue object
        """
        if not venue_data or not venue_data.get('name'):
            return None
        
        venue_name = venue_data.get('name')
        venue = self.Venue.query.filter_by(name=venue_name).first()
        
        if not venue:
            venue = self.Venue(
                name=venue_name,
                location=venue_data.get('location', ''),
                capacity=0,  # Default capacity
                pitch_type='Unknown'  # Default pitch type
            )
            self.db.session.add(venue)
            self.db.session.flush()
            logger.info(f"Created new venue: {venue_name}")
        
        return venue
    
    def _import_players(self, players_data):
        """Import players from match data
        
        Args:
            players_data: List of player data
        """
        for player_data in players_data:
            if not player_data.get('name') or not player_data.get('team_name'):
                continue
            
            # Map Cricbuzz role to our role format
            role = self._map_player_role(player_data.get('role', ''))
            
            # Check if player already exists
            player = self.Player.query.filter_by(name=player_data.get('name'), team_name=player_data.get('team_name')).first()
            
            if player:
                # Update existing player
                player.role = role
                # Update other fields as needed
                logger.debug(f"Updated player: {player.name}")
            else:
                # Create new player
                # Generate reasonable credit points based on role
                credit_points = self._generate_credit_points(role)
                
                # Calculate form based on statistics if available
                current_form = 0.7  # Default form for new players
                if player_data.get('id'):
                    try:
                        form_metrics = self.data_processor.get_player_form(player_data.get('id'))
                        current_form = form_metrics.get('overall_form', 0.7)
                    except Exception:
                        pass
                
                new_player = self.Player(
                    name=player_data.get('name'),
                    team_name=player_data.get('team_name'),
                    role=role,
                    credit_points=credit_points,
                    current_form=current_form
                )
                self.db.session.add(new_player)
                logger.info(f"Created new player: {new_player.name} ({new_player.role}) for {new_player.team_name}")
    
    def _map_player_role(self, cricbuzz_role):
        """Map Cricbuzz player role to our format
        
        Args:
            cricbuzz_role: Role from Cricbuzz API
            
        Returns:
            Mapped role
        """
        role_mapping = {
            'bat': 'Batsman',
            'batsman': 'Batsman',
            'bowl': 'Bowler',
            'bowler': 'Bowler',
            'all': 'All-Rounder',
            'all-rounder': 'All-Rounder',
            'allrounder': 'All-Rounder',
            'wk': 'Wicket-Keeper',
            'wk-batsman': 'Wicket-Keeper',
            'wicket-keeper': 'Wicket-Keeper',
            'keeper': 'Wicket-Keeper'
        }
        
        # Convert to lowercase for case-insensitive matching
        cricbuzz_role_lower = cricbuzz_role.lower()
        
        # Return mapped role or default to Batsman
        for key, value in role_mapping.items():
            if key in cricbuzz_role_lower:
                return value
        
        return 'Batsman'  # Default role
    
    def _generate_credit_points(self, role):
        """Generate reasonable credit points based on player role
        
        Args:
            role: Player role
            
        Returns:
            Credit points
        """
        import random
        
        # Base ranges for different roles
        ranges = {
            'Batsman': (7.5, 9.5),
            'Bowler': (7.5, 9.5),
            'All-Rounder': (8.0, 10.0),
            'Wicket-Keeper': (8.0, 9.0)
        }
        
        # Get range for role or use default
        role_range = ranges.get(role, (7.0, 9.0))
        
        # Generate random value within range (with 0.5 increment)
        value = random.uniform(role_range[0], role_range[1])
        return round(value * 2) / 2  # Round to nearest 0.5
