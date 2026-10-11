"""
Constants for the Dream11 Prediction application.
This file centralizes all constant values used throughout the application.
"""

# Player Roles
class PlayerRoles:
    BATSMAN = "Batsman"
    BOWLER = "Bowler"
    ALL_ROUNDER = "All-Rounder"
    WICKET_KEEPER = "Wicket-Keeper"
    
    # Mapping of various role name formats to standardized versions
    ROLE_MAPPING = {
        "batsman": BATSMAN,
        "bat": BATSMAN,
        "batter": BATSMAN,
        "bowler": BOWLER,
        "bowl": BOWLER,
        "all-rounder": ALL_ROUNDER,
        "all rounder": ALL_ROUNDER,
        "allrounder": ALL_ROUNDER,
        "all_rounder": ALL_ROUNDER,
        "ar": ALL_ROUNDER,
        "wicket-keeper": WICKET_KEEPER,
        "wicket keeper": WICKET_KEEPER,
        "wicketkeeper": WICKET_KEEPER,
        "keeper": WICKET_KEEPER,
        "wk": WICKET_KEEPER,
    }
    
    @classmethod
    def normalize_role(cls, role):
        """Normalize a role name to the standard format"""
        if not role:
            return None
        
        # Check if the role is already in standard format
        if role in [cls.BATSMAN, cls.BOWLER, cls.ALL_ROUNDER, cls.WICKET_KEEPER]:
            return role
        
        # Try to map from the known variations
        normalized = cls.ROLE_MAPPING.get(role.lower())
        if normalized:
            return normalized
        
        # If no mapping found, try to determine based on substring matching
        role_lower = role.lower()
        if "bat" in role_lower:
            return cls.BATSMAN
        elif "bowl" in role_lower:
            return cls.BOWLER
        elif "all" in role_lower and ("round" in role_lower or "rounder" in role_lower):
            return cls.ALL_ROUNDER
        elif "wicket" in role_lower or "keep" in role_lower:
            return cls.WICKET_KEEPER
        
        # Default to batsman if unknown
        return cls.BATSMAN

# Team Generation Strategies
class TeamStrategies:
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    ALL_ROUNDERS = "all_rounders"
    VENUE_SPECIFIC = "venue_specific"
    
    STRATEGY_CHOICES = [
        (BALANCED, "Balanced - Even distribution of players"),
        (AGGRESSIVE, "Aggressive - Focus on batting strength"),
        (DEFENSIVE, "Defensive - Focus on bowling strength"),
        (ALL_ROUNDERS, "All-Rounders - Focus on all-rounders"),
        (VENUE_SPECIFIC, "Venue Specific - Adapt to venue conditions")
    ]
    
    @classmethod
    def get_all_strategies(cls):
        """Return a list of all valid strategy values"""
        return [cls.BALANCED, cls.AGGRESSIVE, cls.DEFENSIVE, cls.ALL_ROUNDERS, cls.VENUE_SPECIFIC]

# Captain Preferences
class CaptainPreferences:
    HIGHEST_POINTS = "highest_points"
    BEST_FORM = "best_form"
    FORM = "form"  # Keep for backward compatibility
    ALL_ROUNDER = "all-rounder"
    BATSMAN = "batsman"
    BOWLER = "bowler"
    SECOND_HIGHEST_POINTS = "second_highest_points"
    DIFFERENT_TEAM = "different_team"
    DIFFERENT_ROLE = "different_role"
    
    CAPTAIN_CHOICES = [
        (HIGHEST_POINTS, "Highest Points - Select player with highest credit points"),
        (BEST_FORM, "Best Form - Select player with best current form"),
        (ALL_ROUNDER, "All-Rounder - Prefer all-rounders for captain"),
        (BATSMAN, "Batsman - Prefer batsmen for captain"),
        (BOWLER, "Bowler - Prefer bowlers for captain")
    ]
    
    VICE_CAPTAIN_CHOICES = [
        (SECOND_HIGHEST_POINTS, "Second Highest Points - Select second highest scoring player"),
        (DIFFERENT_TEAM, "Different Team - Select player from different team than captain"),
        (DIFFERENT_ROLE, "Different Role - Select player with different role than captain")
    ]

# Match Status
class MatchStatus:
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETED = "completed"
    
    STATUS_CHOICES = [
        (UPCOMING, "Upcoming"),
        (LIVE, "Live"),
        (COMPLETED, "Completed")
    ]

# Credit Limits
MAX_CREDITS = 100.0
MAX_TEAM_SIZE = 11
MAX_PLAYERS_FROM_TEAM = 7

# Role Requirements
DEFAULT_ROLE_REQUIREMENTS = {
    PlayerRoles.WICKET_KEEPER: {"min": 1, "max": 1},
    PlayerRoles.BATSMAN: {"min": 3, "max": 5},
    PlayerRoles.BOWLER: {"min": 3, "max": 5},
    PlayerRoles.ALL_ROUNDER: {"min": 1, "max": 3}
}

# Strategy-specific role requirements
STRATEGY_ROLE_REQUIREMENTS = {
    TeamStrategies.BALANCED: DEFAULT_ROLE_REQUIREMENTS,
    TeamStrategies.AGGRESSIVE: {
        PlayerRoles.WICKET_KEEPER: {"min": 1, "max": 2},
        PlayerRoles.BATSMAN: {"min": 4, "max": 6},
        PlayerRoles.BOWLER: {"min": 2, "max": 3},
        PlayerRoles.ALL_ROUNDER: {"min": 1, "max": 3}
    },
    TeamStrategies.DEFENSIVE: {
        PlayerRoles.WICKET_KEEPER: {"min": 1, "max": 1},
        PlayerRoles.BATSMAN: {"min": 2, "max": 4},
        PlayerRoles.BOWLER: {"min": 4, "max": 6},
        PlayerRoles.ALL_ROUNDER: {"min": 1, "max": 3}
    },
    TeamStrategies.VENUE_SPECIFIC: {
        PlayerRoles.WICKET_KEEPER: {"min": 1, "max": 2},
        PlayerRoles.BATSMAN: {"min": 3, "max": 5},
        PlayerRoles.BOWLER: {"min": 3, "max": 5},
        PlayerRoles.ALL_ROUNDER: {"min": 1, "max": 3}
    }
}
