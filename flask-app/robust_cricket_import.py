"""
Robust Cricket Data Import Script
- Verifies working API endpoints before using them
- Creates fallback data if API fails
- Ensures the application works regardless of API status
"""

import http.client
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from app import app, db
from src.models import Match, Player, Team, User, Venue
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustCricbuzzAPI:
    """API client that verifies endpoints before using them"""
    
    def __init__(self, api_key=os.environ["RAPIDAPI_KEY"]):
        self.api_key = api_key
        self.host = "cricbuzz-cricket.p.rapidapi.com"
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': self.host
        }
        # Track verified endpoints
        self.verified_endpoints = set()
        # Save working match IDs
        self.working_match_ids = []
    
    def verify_endpoint(self, endpoint):
        """Test if an endpoint is working"""
        conn = http.client.HTTPSConnection(self.host)
        try:
            conn.request("GET", endpoint, headers=self.headers)
            response = conn.getresponse()
            
            if response.status == 200:
                data = response.read().decode("utf-8")
                try:
                    # Check if response is valid JSON
                    json_data = json.loads(data)
                    self.verified_endpoints.add(endpoint)
                    return json_data
                except json.JSONDecodeError:
                    logger.warning(f"Endpoint {endpoint} returned non-JSON response")
                    return None
            else:
                logger.warning(f"Endpoint {endpoint} returned status code {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error accessing endpoint {endpoint}: {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_data(self, endpoint):
        """Get data from an endpoint, verifying it first if needed"""
        if endpoint not in self.verified_endpoints:
            result = self.verify_endpoint(endpoint)
            if result is None:
                return None
            return result
        
        # Endpoint already verified, use it directly
        conn = http.client.HTTPSConnection(self.host)
        try:
            conn.request("GET", endpoint, headers=self.headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error accessing verified endpoint {endpoint}: {str(e)}")
            return None
        finally:
            conn.close()
    
    def find_working_match_ids(self):
        """Find match IDs that are accessible through the API"""
        working_ids = []
        
        # Check upcoming matches
        upcoming_data = self.get_data("/matches/v1/upcoming")
        if upcoming_data:
            logger.info("Successfully accessed upcoming matches endpoint")
            # Extract match IDs from the response
            try:
                for match_type in upcoming_data.get("typeMatches", []):
                    for series_matches in match_type.get("seriesMatches", []):
                        for match in series_matches.get("seriesAdWrapper", {}).get("matches", []):
                            match_id = match.get("matchInfo", {}).get("matchId")
                            if match_id:
                                working_ids.append(str(match_id))
            except Exception as e:
                logger.error(f"Error extracting match IDs from upcoming matches: {str(e)}")
        
        # Check live matches
        live_data = self.get_data("/matches/v1/live")
        if live_data:
            logger.info("Successfully accessed live matches endpoint")
            # Extract match IDs from the response
            try:
                for match_type in live_data.get("typeMatches", []):
                    for series_matches in match_type.get("seriesMatches", []):
                        for match in series_matches.get("seriesAdWrapper", {}).get("matches", []):
                            match_id = match.get("matchInfo", {}).get("matchId")
                            if match_id:
                                working_ids.append(str(match_id))
            except Exception as e:
                logger.error(f"Error extracting match IDs from live matches: {str(e)}")
        
        # Check recent matches
        recent_data = self.get_data("/matches/v1/recent")
        if recent_data:
            logger.info("Successfully accessed recent matches endpoint")
            # Extract match IDs from the response
            try:
                for match_type in recent_data.get("typeMatches", []):
                    for series_matches in match_type.get("seriesMatches", []):
                        for match in series_matches.get("seriesAdWrapper", {}).get("matches", []):
                            match_id = match.get("matchInfo", {}).get("matchId")
                            if match_id:
                                working_ids.append(str(match_id))
            except Exception as e:
                logger.error(f"Error extracting match IDs from recent matches: {str(e)}")
        
        # Save the working IDs
        self.working_match_ids = working_ids
        logger.info(f"Found {len(working_ids)} working match IDs")
        
        # Test a few match IDs to make sure they're accessible
        verified_ids = []
        for match_id in working_ids[:5]:  # Test first 5 matches
            match_data = self.get_data(f"/mcenter/v1/{match_id}/info")
            if match_data:
                logger.info(f"Successfully accessed match info for match ID {match_id}")
                verified_ids.append(match_id)
        
        logger.info(f"Verified {len(verified_ids)} out of {min(5, len(working_ids))} test match IDs")
        return working_ids

def create_sample_data():
    """Create sample data for the application if API fails"""
    logger.info("Creating sample data for the application")
    
    with app.app_context():
        # Create sample venues
        venues = [
            Venue(name="Wankhede Stadium", city="Mumbai", country="India", capacity=33000),
            Venue(name="Eden Gardens", city="Kolkata", country="India", capacity=66000),
            Venue(name="M. Chinnaswamy Stadium", city="Bangalore", country="India", capacity=40000),
            Venue(name="Narendra Modi Stadium", city="Ahmedabad", country="India", capacity=132000),
            Venue(name="MA Chidambaram Stadium", city="Chennai", country="India", capacity=50000)
        ]
        
        for venue in venues:
            db.session.add(venue)
        db.session.commit()
        logger.info(f"Created {len(venues)} sample venues")
        
        # Create sample teams
        teams = ["Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
                "Delhi Capitals", "Kolkata Knight Riders", "Punjab Kings", 
                "Rajasthan Royals", "Sunrisers Hyderabad", "Gujarat Titans", "Lucknow Super Giants"]
        
        # Create upcoming matches
        upcoming_matches = []
        for i in range(10):
            team1, team2 = random.sample(teams, 2)
            match_date = datetime.now() + timedelta(days=random.randint(1, 7))
            venue = random.choice(venues)
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="upcoming",
                venue_id=venue.id,
                external_id=f"SAMPLE_UPC_{i+100}",
                format="T20",
                series_name="IPL 2025"
            )
            upcoming_matches.append(match)
        
        # Create live matches
        live_matches = []
        for i in range(2):
            team1, team2 = random.sample(teams, 2)
            match_date = datetime.now()
            venue = random.choice(venues)
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="live",
                venue_id=venue.id,
                external_id=f"SAMPLE_LIVE_{i+200}",
                format="T20",
                series_name="IPL 2025"
            )
            live_matches.append(match)
        
        # Create completed matches
        completed_matches = []
        for i in range(5):
            team1, team2 = random.sample(teams, 2)
            match_date = datetime.now() - timedelta(days=random.randint(1, 7))
            venue = random.choice(venues)
            winner = random.choice([team1, team2])
            
            match = Match(
                team1=team1,
                team2=team2,
                date=match_date,
                status="completed",
                result=f"{winner} won by {random.randint(1, 8)} {'wickets' if random.random() > 0.5 else 'runs'}",
                venue_id=venue.id,
                external_id=f"SAMPLE_COMP_{i+300}",
                format="T20",
                series_name="IPL 2025"
            )
            completed_matches.append(match)
        
        # Add all matches to database
        for match in upcoming_matches + live_matches + completed_matches:
            db.session.add(match)
        db.session.commit()
        logger.info(f"Created {len(upcoming_matches)} upcoming matches, {len(live_matches)} live matches, and {len(completed_matches)} completed matches")
        
        # Create sample players for all teams
        player_roles = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
        players_created = 0
        
        for team in teams:
            for i in range(15):  # 15 players per team
                role = random.choice(player_roles)
                form = round(random.uniform(0.4, 0.9), 2)
                
                player = Player(
                    name=f"{team[:3]}_Player{i+1}",
                    team_name=team,
                    role=role,
                    credit_value=round(random.uniform(7.0, 10.5), 1),
                    current_form=form
                )
                db.session.add(player)
                players_created += 1
        
        db.session.commit()
        logger.info(f"Created {players_created} sample players")
        
        # Add admin user if it doesn't exist
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@example.com",
                is_admin=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            logger.info("Created admin user")
        
        logger.info("Sample data creation completed successfully")

def import_api_data(api):
    """Import data from the API if it's working"""
    logger.info("Importing data from Cricbuzz API")
    
    # First check if we can access the API and find working match IDs
    working_ids = api.find_working_match_ids()
    
    if not working_ids:
        logger.warning("No working match IDs found from the API")
        return False
    
    logger.info(f"Found {len(working_ids)} working match IDs")
    
    with app.app_context():
        # Create venues as we process matches
        venues = {}
        
        # Process each match ID
        matches_imported = 0
        players_imported = 0
        venues_imported = 0
        
        for match_id in working_ids:
            try:
                # Get match info
                match_info_data = api.get_data(f"/mcenter/v1/{match_id}/info")
                
                if not match_info_data or "matchInfo" not in match_info_data:
                    logger.warning(f"Could not get info for match ID {match_id}")
                    continue
                
                match_info = match_info_data.get("matchInfo", {})
                venue_info = match_info.get("venueInfo", {})
                
                # Get or create venue
                venue_name = venue_info.get("ground", "Unknown Venue")
                if venue_name in venues:
                    venue = venues[venue_name]
                else:
                    venue = Venue.query.filter_by(name=venue_name).first()
                    if not venue:
                        venue = Venue(
                            name=venue_name,
                            city=venue_info.get("city", "Unknown City"),
                            country=venue_info.get("country", "Unknown Country"),
                            capacity=random.randint(20000, 50000)
                        )
                        db.session.add(venue)
                        db.session.commit()
                        venues_imported += 1
                    
                    venues[venue_name] = venue
                
                # Create match
                team1_name = match_info.get("team1", {}).get("teamName", "Unknown Team")
                team2_name = match_info.get("team2", {}).get("teamName", "Unknown Team")
                
                # Check if match already exists
                existing_match = Match.query.filter_by(external_id=str(match_id)).first()
                if existing_match:
                    match = existing_match
                    logger.info(f"Updating existing match: {team1_name} vs {team2_name}")
                else:
                    match = Match()
                    logger.info(f"Creating new match: {team1_name} vs {team2_name}")
                
                # Parse match date and time
                try:
                    match_date_str = match_info.get("matchDate", "")
                    match_time_str = match_info.get("matchTime", "")
                    if match_date_str:
                        # Try different date formats
                        try:
                            match_date = datetime.strptime(f"{match_date_str} {match_time_str}", "%Y-%m-%d %H:%M")
                        except:
                            try:
                                match_date = datetime.strptime(match_date_str, "%Y-%m-%d")
                            except:
                                match_date = datetime.now()
                    else:
                        match_date = datetime.now()
                except Exception as e:
                    logger.warning(f"Error parsing match date: {str(e)}")
                    match_date = datetime.now()
                
                # Update match properties
                match.team1 = team1_name
                match.team2 = team2_name
                match.date = match_date
                match.venue_id = venue.id
                match.external_id = str(match_id)
                match.series_name = match_info.get("seriesName", "Unknown Series")
                match.format = match_info.get("matchFormat", "T20")
                
                # Set match status
                status = match_info.get("state", "").lower()
                if status == "complete":
                    match.status = "completed"
                    match.result = match_info.get("status", "Unknown result")
                elif status == "inprogress":
                    match.status = "live"
                else:
                    match.status = "upcoming"
                
                # Save match to database
                if not existing_match:
                    db.session.add(match)
                db.session.commit()
                matches_imported += 1
                
                # Import players if available in squads
                if "teamPlayers" in match_info_data:
                    for team_data in match_info_data.get("teamPlayers", []):
                        team_id = team_data.get("teamId", "")
                        if str(team_id) == str(match_info.get("team1", {}).get("teamId", "")):
                            team_name = team1_name
                        else:
                            team_name = team2_name
                        
                        for player_data in team_data.get("players", []):
                            player_name = player_data.get("name", "Unknown Player")
                            player_role = player_data.get("role", "").lower()
                            
                            # Map role
                            if "bat" in player_role:
                                role = "Batsman"
                            elif "bowl" in player_role:
                                role = "Bowler"
                            elif "all" in player_role:
                                role = "All-Rounder"
                            elif "wk" in player_role:
                                role = "Wicket-Keeper"
                            else:
                                role = "All-Rounder"
                            
                            # Check if player exists
                            player = Player.query.filter_by(name=player_name, team_name=team_name).first()
                            if not player:
                                player = Player(
                                    name=player_name,
                                    team_name=team_name,
                                    role=role,
                                    credit_value=round(random.uniform(7.0, 10.5), 1),
                                    current_form=round(random.uniform(0.5, 0.9), 2)
                                )
                                db.session.add(player)
                                players_imported += 1
                    
                    db.session.commit()
            
            except Exception as e:
                logger.error(f"Error processing match ID {match_id}: {str(e)}")
        
        logger.info(f"API Import Summary: {matches_imported} matches, {players_imported} players, {venues_imported} venues")
        return matches_imported > 0

def handle_data_import():
    """Handle data import, with fallback to sample data if API fails"""
    # Initialize the API
    api = RobustCricbuzzAPI()
    
    with app.app_context():
        # Check if database already has data
        existing_matches = Match.query.count()
        existing_players = Player.query.count()
        
        logger.info(f"Found {existing_matches} existing matches and {existing_players} existing players in database")
        
        # If database already has substantial data, just return
        if existing_matches > 10 and existing_players > 50:
            logger.info("Database already has sufficient data, skipping import")
            return True
        
        # Try to import from API first
        api_success = import_api_data(api)
        
        # If API import failed, or we didn't get enough data, create sample data
        if not api_success:
            logger.warning("API import failed or returned insufficient data, creating sample data")
            create_sample_data()
        
        # Final check
        with app.app_context():
            final_matches = Match.query.count()
            final_players = Player.query.count()
            final_venues = Venue.query.count()
            
            logger.info(f"Final database state: {final_matches} matches, {final_players} players, {final_venues} venues")
            
            # Ensure we have the admin user
            if not User.query.filter_by(username="admin").first():
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    is_admin=True
                )
                admin.set_password("admin123")
                db.session.add(admin)
                db.session.commit()
                logger.info("Created admin user")
            
            return final_matches > 0 and final_players > 0

if __name__ == "__main__":
    logger.info("Starting Dream11 Prediction data import")
    success = handle_data_import()
    if success:
        logger.info("Data import completed successfully")
        print("Dream11 Prediction app data import completed successfully. The app is ready to use!")
        sys.exit(0)
    else:
        logger.error("Data import failed")
        print("Dream11 Prediction app data import failed. Please check the logs for details.")
        sys.exit(1)
