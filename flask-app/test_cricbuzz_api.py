"""
Test script for Cricbuzz API connectivity and response format.
Uses the exact code provided by the user to test direct API connection.
"""

import http.client
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_api_call():
    """Test the direct API call using the user-provided code"""
    logger.info("Testing direct API call to Cricbuzz")
    
    # Using the exact code provided by the user
    conn = http.client.HTTPSConnection("cricbuzz-cricket.p.rapidapi.com")
    
    headers = {
        'x-rapidapi-key': os.environ["RAPIDAPI_KEY"],
        'x-rapidapi-host': "cricbuzz-cricket.p.rapidapi.com"
    }
    
    try:
        # Test with the commentary endpoint first
        conn.request("GET", "/mcenter/v1/41881/comm", headers=headers)
        
        res = conn.getresponse()
        data = res.read()
        
        # Check if we got a valid response
        status_code = res.status
        logger.info(f"API Response Status: {status_code}")
        
        if status_code == 200:
            logger.info("API call successful!")
            # Try to parse the JSON to validate response format
            try:
                json_data = json.loads(data.decode("utf-8"))
                logger.info("Response is valid JSON")
                logger.info(f"Response keys: {list(json_data.keys())}")
            except json.JSONDecodeError:
                logger.error("Could not parse response as JSON")
                logger.info(data.decode("utf-8")[:500])  # Show first 500 chars
        else:
            logger.error(f"API call failed with status code: {status_code}")
            logger.error(data.decode("utf-8"))
        
        # Try another API endpoint if the first one failed
        if status_code != 200:
            logger.info("Trying alternate endpoint (matches list)...")
            conn.request("GET", "/matches/v1/upcoming", headers=headers)
            
            res = conn.getresponse()
            data = res.read()
            
            status_code = res.status
            logger.info(f"Alternate API Response Status: {status_code}")
            
            if status_code == 200:
                logger.info("Alternate API call successful!")
                try:
                    json_data = json.loads(data.decode("utf-8"))
                    logger.info("Response is valid JSON")
                    logger.info(f"Response keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'List response'}")
                except json.JSONDecodeError:
                    logger.error("Could not parse response as JSON")
                    logger.info(data.decode("utf-8")[:500])
            else:
                logger.error(f"Alternate API call failed with status code: {status_code}")
                logger.error(data.decode("utf-8"))
    
    except Exception as e:
        logger.error(f"Error during API call: {str(e)}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_direct_api_call()
