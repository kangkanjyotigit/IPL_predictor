"""
Direct Cricbuzz API integration using http.client
This implementation uses the exact connection method provided by the user
"""

import http.client
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

logger = logging.getLogger(__name__)

class DirectCricbuzzAPI:
    """
    Direct implementation of Cricbuzz API using http.client as provided by the user
    This bypasses any issues with the existing implementation
    """
    
    def __init__(self, api_key=os.environ["RAPIDAPI_KEY"]):
        """Initialize with the RapidAPI key"""
        self.api_key = api_key
        self.base_host = "cricbuzz-cricket.p.rapidapi.com"
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': self.base_host
        }
    
    def verify_endpoint(self, endpoint: str) -> bool:
        """
        Verify if an endpoint is working - minimal implementation to reduce API calls
        Args:
            endpoint: API endpoint to check
            
        Returns:
            True if endpoint is working, False otherwise
        """
        # Skip verification for most endpoints to reduce API calls
        # We'll assume they're working and handle failures when they actually occur
        if not hasattr(self, '_verified_cache'):
            self._verified_cache = {}
        
        # Return cached result if available
        if endpoint in self._verified_cache:
            return self._verified_cache[endpoint]
            
        # Only verify if it's a critical endpoint or not yet verified
        if '/matches/v1/' in endpoint:
            # Assume matches endpoint works without making an API call
            self._verified_cache[endpoint] = True
            return True
        
        # For other endpoints, verify only once and cache the result
        conn = http.client.HTTPSConnection(self.base_host)
        
        try:
            conn.request("GET", endpoint, headers=self.headers)
            res = conn.getresponse()
            
            status_code = res.status
            is_working = status_code == 200
            self._verified_cache[endpoint] = is_working
            
            if is_working:
                logger.info(f"API endpoint {endpoint} is available")
            else:
                logger.warning(f"API endpoint {endpoint} returned status {status_code}")
                
            return is_working
        except Exception as e:
            logger.error(f"Error verifying API endpoint {endpoint}: {str(e)}")
            self._verified_cache[endpoint] = False
            return False
        finally:
            conn.close()
    
    def _make_api_request(self, endpoint: str) -> Dict:
        """
        Make a direct API request using http.client
        Args:
            endpoint: API endpoint path
            
        Returns:
            JSON response as dict
        """
        if not self.verify_endpoint(endpoint):
            return {"error": f"API endpoint {endpoint} is not available"}
        
        conn = http.client.HTTPSConnection(self.base_host)
        
        try:
            conn.request("GET", endpoint, headers=self.headers)
            res = conn.getresponse()
            data = res.read()
            
            status_code = res.status
            if status_code == 200:
                return json.loads(data.decode("utf-8"))
            else:
                logger.error(f"API request failed with status {status_code}: {data.decode('utf-8')}")
                return {"error": f"API request failed with status {status_code}"}
                
        except Exception as e:
            logger.exception(f"Error during API request to {endpoint}: {str(e)}")
            return {"error": str(e)}
        
        finally:
            conn.close()
    
    def get_match_commentary(self, match_id: str) -> Dict:
        """Get commentary for a specific match"""
        endpoint = f"/mcenter/v1/{match_id}/comm"
        return self._make_api_request(endpoint)
    
    def get_match_info(self, match_id: str) -> Dict:
        """Get detailed information for a specific match"""
        endpoint = f"/mcenter/v1/{match_id}/info"
        return self._make_api_request(endpoint)
    
    def get_match_scorecard(self, match_id: str) -> Dict:
        """Get scorecard for a specific match"""
        endpoint = f"/mcenter/v1/{match_id}/scard"
        return self._make_api_request(endpoint)
        
    def get_upcoming_matches(self) -> Dict:
        """Get list of upcoming matches"""
        endpoint = "/matches/v1/upcoming"
        return self._make_api_request(endpoint)
    
    def get_live_matches(self) -> Dict:
        """Get list of live matches"""
        endpoint = "/matches/v1/live"
        return self._make_api_request(endpoint)
    
    def get_recent_matches(self) -> Dict:
        """Get list of recent matches"""
        endpoint = "/matches/v1/recent"
        return self._make_api_request(endpoint)
    
    def get_series_matches(self, series_id: str) -> Dict:
        """Get matches for a specific series"""
        endpoint = f"/series/v1/{series_id}/matches"
        return self._make_api_request(endpoint)
    
    def get_series_list(self) -> Dict:
        """Get list of cricket series"""
        endpoint = "/series/v1/international"
        return self._make_api_request(endpoint)
    
    def get_player_info(self, player_id: str) -> Dict:
        """Get information for a specific player"""
        endpoint = f"/stats/v1/player/info/{player_id}"
        return self._make_api_request(endpoint)
    
    def get_player_stats(self, player_id: str) -> Dict:
        """Get statistics for a specific player"""
        endpoint = f"/stats/v1/player/{player_id}"
        return self._make_api_request(endpoint)
    
    def search_players(self, name: str) -> Dict:
        """Search for players by name"""
        endpoint = f"/stats/v1/player/search?plrN={name}"
        return self._make_api_request(endpoint)
