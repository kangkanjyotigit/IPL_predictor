"""
Import live cricket match data using direct Cricbuzz API integration.
This script uses the working API implementation to populate the database.
"""

from app import app, db
from src.models import Match, Player, Venue
from src.services.direct_api import DirectCricbuzzAPI
import logging
from datetime import datetime
import random
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_live_cricket_data():
    """Import real cricket match data using the working direct API implementation"""
    
    # Initialize the direct API implementation that we've confirmed works
    api = DirectCricbuzzAPI(api_key=os.environ["RAPIDAPI_KEY"])
    
    with app.app_context():
        try:
            # First try to get live matches
            logger.info("Fetching live matches from Cricbuzz API...")
            live_matches = api.get_live_matches()
            
            if "typeMatches" not in live_matches:
                logger.warning("No live matches found or unexpected API response format")
                live_matches = {"typeMatches": []}
            
            # Then get upcoming matches
            logger.info("Fetching upcoming matches from Cricbuzz API...")
            upcoming_matches = api.get_upcoming_matches()
            
            if "typeMatches" not in upcoming_matches:
                logger.warning("No upcoming matches found or unexpected API response format")
                upcoming_matches = {"typeMatches": []}
            
            # Then get recent matches
            logger.info("Fetching recent matches from Cricbuzz API...")
            recent_matches = api.get_recent_matches()
            
            if "typeMatches" not in recent_matches:
                logger.warning("No recent matches found or unexpected API response format")
                recent_matches = {"typeMatches": []}
            
            # Process all matches from the three categories
            matches_to_process = []
            
            # Process each category and compile a list of match IDs to fetch details for
            for matches_data in [live_matches, upcoming_matches, recent_matches]:
                for match_type in matches_data.get("typeMatches", []):
                    for series_matches in match_type.get("seriesMatches", []):
                        for match in series_matches.get("seriesAdWrapper", {}).get("matches", []):
                            match_info = match.get("matchInfo", {})
                            match_id = match_info.get("matchId")
                            
                            if match_id:
                                # Add to our processing list if not already there
                                if match_id not in [m.get("id") for m in matches_to_process]:
                                    matches_to_process.append({
                                        "id": match_id,
                                        "team1": match_info.get("team1", {}).get("teamName", "Unknown Team"),
                                        "team2": match_info.get("team2", {}).get("teamName", "Unknown Team"),
                                        "series": match_info.get("seriesName", "Unknown Series"),
                                        "status": match_info.get("status", "upcoming")
                                    })
            
            logger.info(f"Found {len(matches_to_process)} matches to import")
            
            # Process each match and import to database
            successful_imports = 0
            for match_data in matches_to_process:
                try:
                    match_id = match_data["id"]
                    logger.info(f"Processing match ID {match_id}: {match_data['team1']} vs {match_data['team2']}")
                    
                    # Get detailed match info
                    match_details = api.get_match_info(match_id)
                    
                    # If we got a valid response
                    if "matchInfo" in match_details:
                        match_info = match_details["matchInfo"]
                        venue_info = match_info.get("venueInfo", {})
                        
                        # Create or get venue first
                        venue = Venue.query.filter_by(name=venue_info.get("ground", "Unknown Venue")).first()
                        if not venue:
                            venue = Venue(
                                name=venue_info.get("ground", "Unknown Venue"),
                                city=venue_info.get("city", "Unknown City"),
                                country=venue_info.get("country", "Unknown Country"),
                                capacity=random.randint(20000, 50000)  # We don't have this info from API
                            )
                            db.session.add(venue)
                            db.session.commit()
                            logger.info(f"Created new venue: {venue.name}")
                        
                        # Check if match already exists
                        existing_match = Match.query.filter_by(external_id=str(match_id)).first()
                        if existing_match:
                            logger.info(f"Match ID {match_id} already exists in database, updating...")
                            match_obj = existing_match
                        else:
                            match_obj = Match()
                            logger.info(f"Creating new match record for match ID {match_id}")
                        
                        # Update match details
                        match_obj.team1 = match_data["team1"]
                        match_obj.team2 = match_data["team2"]
                        match_obj.external_id = str(match_id)
                        match_obj.venue_id = venue.id
                        match_obj.series_name = match_data["series"]
                        
                        # Parse match date
                        try:
                            match_date_str = match_info.get("matchDate", "")
                            match_time_str = match_info.get("matchTime", "")
                            if match_date_str:
                                # Format may vary, try common formats
                                match_obj.date = datetime.strptime(f"{match_date_str} {match_time_str}", "%Y-%m-%d %H:%M")
                            else:
                                match_obj.date = datetime.now()
                        except Exception as date_error:
                            logger.warning(f"Error parsing match date: {str(date_error)}")
                            match_obj.date = datetime.now()
                        
                        # Match status and result
                        match_obj.status = match_data["status"].lower()
                        if match_obj.status == "complete":
                            match_obj.status = "completed"
                        
                        # Get result if match is completed
                        if match_obj.status == "completed":
                            try:
                                match_obj.result = match_info.get("status", "Unknown result")
                            except:
                                match_obj.result = "Unknown result"
                        
                        # Match format
                        match_obj.format = match_info.get("matchFormat", "T20")
                        
                        # Save match to database
                        if not existing_match:
                            db.session.add(match_obj)
                        db.session.commit()
                        
                        # Process players from both teams
                        successful_imports += 1
                        logger.info(f"Successfully imported match: {match_obj.team1} vs {match_obj.team2}")
                        
                        # Now try to get player data from the match
                        try:
                            team1_id = match_info.get("team1", {}).get("teamId", "")
                            team2_id = match_info.get("team2", {}).get("teamId", "")
                            
                            # Look for players in the match info or try to get detailed scorecard
                            if "squad" in match_details:
                                # Process players from squad if available
                                for team_squad in match_details.get("squad", []):
                                    team_id = team_squad.get("teamId", "")
                                    team_name = match_obj.team1 if str(team_id) == str(team1_id) else match_obj.team2
                                    
                                    for player_info in team_squad.get("squadPlayers", []):
                                        player_id = player_info.get("id", "")
                                        player_name = player_info.get("name", "Unknown Player")
                                        player_role = player_info.get("role", "Unknown Role")
                                        
                                        # Map raw role to our role categories
                                        role_mapping = {
                                            "bat": "Batsman",
                                            "bowl": "Bowler",
                                            "all": "All-Rounder",
                                            "wk": "Wicket-Keeper",
                                            "wk-bat": "Wicket-Keeper"
                                        }
                                        
                                        mapped_role = role_mapping.get(player_role.lower(), "All-Rounder")
                                        
                                        # Check if player already exists
                                        existing_player = Player.query.filter_by(
                                            name=player_name, 
                                            team_name=team_name
                                        ).first()
                                        
                                        if not existing_player:
                                            # Create new player
                                            player = Player(
                                                name=player_name,
                                                team_name=team_name,
                                                role=mapped_role,
                                                credit_value=round(random.uniform(7.0, 10.5), 1),  # Random credit value
                                                current_form=round(random.uniform(0.5, 0.9), 2)    # Random form
                                            )
                                            db.session.add(player)
                                            logger.info(f"Added player {player_name} ({mapped_role}) to {team_name}")
                                
                                db.session.commit()
                                logger.info(f"Added players for match {match_id}")
                            else:
                                logger.warning(f"No squad information available for match {match_id}")
                                
                        except Exception as player_error:
                            logger.error(f"Error processing players for match {match_id}: {str(player_error)}")
                    
                    else:
                        logger.warning(f"Could not get detailed info for match {match_id}")
                        
                except Exception as match_error:
                    logger.error(f"Error processing match {match_data.get('id', 'unknown')}: {str(match_error)}")
            
            logger.info(f"Successfully imported {successful_imports} out of {len(matches_to_process)} matches")
            
            # Add sample players for teams that don't have any players yet
            for team_name in set([m.team1 for m in Match.query.all()] + [m.team2 for m in Match.query.all()]):
                player_count = Player.query.filter_by(team_name=team_name).count()
                
                if player_count < 5:
                    logger.info(f"Team {team_name} has only {player_count} players, adding sample players")
                    roles = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
                    
                    # Add some sample players
                    for i in range(11 - player_count):
                        role = roles[i % len(roles)]
                        player = Player(
                            name=f"{team_name[:3]}_Player{i+1}",
                            team_name=team_name,
                            role=role,
                            credit_value=round(random.uniform(7.0, 10.5), 1),
                            current_form=round(random.uniform(0.5, 0.9), 2)
                        )
                        db.session.add(player)
                    
                    db.session.commit()
                    logger.info(f"Added sample players for team {team_name}")
            
            # Summary of what's in the database
            matches_count = Match.query.count()
            players_count = Player.query.count()
            venues_count = Venue.query.count()
            
            logger.info("===== DATABASE SUMMARY =====")
            logger.info(f"Total matches: {matches_count}")
            logger.info(f"Total players: {players_count}")
            logger.info(f"Total venues: {venues_count}")
            logger.info("===========================")
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing cricket data: {str(e)}")
            return False

if __name__ == "__main__":
    success = import_live_cricket_data()
    if success:
        print("Successfully imported live cricket data!")
        sys.exit(0)
    else:
        print("Failed to import live cricket data.")
        sys.exit(1)
