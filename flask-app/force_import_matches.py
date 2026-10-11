"""
Force Import Cricket Matches
This script directly connects to the Cricbuzz API and imports matches while
explicitly bypassing any caching or other mechanisms that might be causing issues.
"""

import http.client
import json
import logging
import os
import sys
from datetime import datetime
from app import app, db
from src.models import Match, Player, Venue, Team

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def direct_api_call(endpoint):
    """Make a direct API call to Cricbuzz"""
    conn = http.client.HTTPSConnection("cricbuzz-cricket.p.rapidapi.com")
    
    headers = {
        'x-rapidapi-key': os.environ["RAPIDAPI_KEY"],
        'x-rapidapi-host': "cricbuzz-cricket.p.rapidapi.com"
    }
    
    try:
        conn.request("GET", endpoint, headers=headers)
        response = conn.getresponse()
        
        if response.status == 200:
            data = json.loads(response.read().decode("utf-8"))
            return data
        else:
            logger.error(f"API error: {response.status} - {response.read().decode('utf-8')}")
            return None
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return None
    finally:
        conn.close()

def reset_database():
    """Clear existing matches, players and venues"""
    with app.app_context():
        # Delete all existing records
        try:
            logger.info("Deleting existing records...")
            Team.query.delete()
            Player.query.delete()
            Match.query.delete()
            Venue.query.delete()
            db.session.commit()
            logger.info("Database cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing database: {str(e)}")
            db.session.rollback()

def import_matches():
    """Import matches from Cricbuzz API"""
    # First get upcoming matches
    logger.info("Fetching upcoming matches...")
    upcoming_data = direct_api_call("/matches/v1/upcoming")
    
    # Then get live matches
    logger.info("Fetching live matches...")
    live_data = direct_api_call("/matches/v1/live")
    
    # Then get recent matches
    logger.info("Fetching recent matches...")
    recent_data = direct_api_call("/matches/v1/recent")
    
    all_matches = []
    match_ids = set()
    
    # Process all match types
    for matches_data in [upcoming_data, live_data, recent_data]:
        if not matches_data:
            continue
            
        if "typeMatches" not in matches_data:
            logger.warning("Unexpected API response format")
            continue
            
        # Extract matches
        for match_type in matches_data.get("typeMatches", []):
            for series_matches in match_type.get("seriesMatches", []):
                for match in series_matches.get("seriesAdWrapper", {}).get("matches", []):
                    match_info = match.get("matchInfo", {})
                    match_id = match_info.get("matchId")
                    
                    if match_id and match_id not in match_ids:
                        match_ids.add(match_id)
                        all_matches.append({
                            "id": match_id,
                            "team1": match_info.get("team1", {}).get("teamName", "Unknown Team"),
                            "team2": match_info.get("team2", {}).get("teamName", "Unknown Team"),
                            "series": match_info.get("seriesName", "Unknown Series"),
                            "date": match_info.get("startDate", ""),
                            "venue": match_info.get("venueInfo", {}).get("ground", "Unknown Venue"),
                            "city": match_info.get("venueInfo", {}).get("city", "Unknown City"),
                            "country": match_info.get("venueInfo", {}).get("country", "Unknown Country"),
                            "format": match_info.get("matchFormat", "T20"),
                            "status": match_info.get("status", "upcoming")
                        })
    
    logger.info(f"Found {len(all_matches)} unique matches")
    
    # Save matches to database
    with app.app_context():
        for match_data in all_matches:
            try:
                # First create or get venue
                venue = Venue.query.filter_by(name=match_data["venue"]).first()
                if not venue:
                    venue = Venue(
                        name=match_data["venue"],
                        city=match_data["city"],
                        country=match_data["country"],
                        capacity=50000  # Default capacity
                    )
                    db.session.add(venue)
                    db.session.commit()
                
                # Create match
                match = Match(
                    team1=match_data["team1"],
                    team2=match_data["team2"],
                    external_id=str(match_data["id"]),
                    venue_id=venue.id,
                    series_name=match_data["series"],
                    format=match_data["format"],
                    status=match_data["status"].lower(),
                    date=datetime.fromtimestamp(int(match_data["date"])/1000) if match_data["date"] else datetime.now()
                )
                
                db.session.add(match)
                db.session.commit()
                logger.info(f"Added match: {match_data['team1']} vs {match_data['team2']}")
                
                # Add players for the teams if they don't exist yet
                if not Player.query.filter_by(team_name=match_data["team1"]).first():
                    add_sample_players(match_data["team1"])
                    
                if not Player.query.filter_by(team_name=match_data["team2"]).first():
                    add_sample_players(match_data["team2"])
                    
            except Exception as e:
                logger.error(f"Error saving match {match_data['team1']} vs {match_data['team2']}: {str(e)}")
                db.session.rollback()

def add_sample_players(team_name):
    """Add sample players for a team"""
    logger.info(f"Adding sample players for {team_name}")
    
    roles = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
    batsmen = [f"{team_name[:3]}_{name}" for name in ["Sharma", "Kohli", "Williamson", "Smith", "Root"]]
    bowlers = [f"{team_name[:3]}_{name}" for name in ["Bumrah", "Cummins", "Starc", "Anderson", "Rabada"]]
    all_rounders = [f"{team_name[:3]}_{name}" for name in ["Jadeja", "Stokes", "Pandya", "Maxwell", "Russell"]]
    keepers = [f"{team_name[:3]}_{name}" for name in ["Dhoni", "Buttler", "Rizwan", "Carey"]]
    
    with app.app_context():
        try:
            # Add batsmen
            for name in batsmen:
                player = Player(
                    name=name,
                    team_name=team_name,
                    role="Batsman",
                    credit_value=9.5,
                    current_form=0.85
                )
                db.session.add(player)
            
            # Add bowlers
            for name in bowlers:
                player = Player(
                    name=name,
                    team_name=team_name,
                    role="Bowler",
                    credit_value=9.0,
                    current_form=0.8
                )
                db.session.add(player)
            
            # Add all-rounders
            for name in all_rounders:
                player = Player(
                    name=name,
                    team_name=team_name,
                    role="All-Rounder",
                    credit_value=10.0,
                    current_form=0.9
                )
                db.session.add(player)
            
            # Add wicket-keepers
            for name in keepers:
                player = Player(
                    name=name,
                    team_name=team_name,
                    role="Wicket-Keeper",
                    credit_value=9.0,
                    current_form=0.8
                )
                db.session.add(player)
            
            db.session.commit()
            logger.info(f"Added players for {team_name}")
        except Exception as e:
            logger.error(f"Error adding players for {team_name}: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("Starting force import of cricket matches")
    
    # First reset the database
    reset_database()
    
    # Import matches
    import_matches()
    
    # Summary of what's in the database
    with app.app_context():
        matches_count = Match.query.count()
        players_count = Player.query.count() 
        venues_count = Venue.query.count()
        
        logger.info("===== DATABASE SUMMARY =====")
        logger.info(f"Total matches: {matches_count}")
        logger.info(f"Total players: {players_count}")
        logger.info(f"Total venues: {venues_count}")
        logger.info("===========================")
    
    logger.info("Force import completed!")
    print("✅ Force import of cricket matches completed successfully!")
