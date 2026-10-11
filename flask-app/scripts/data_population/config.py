"""Configuration for data population"""

# API Configuration
CRICAPI_KEY = "YOUR_CRICAPI_KEY"  # Replace with actual API key
CRICAPI_BASE_URL = "https://api.cricapi.com/v1"

# Data Population Configuration
TOP_TEAMS = [
    {'name': 'India', 'country': 'India', 'ranking': 1},
    {'name': 'Australia', 'country': 'Australia', 'ranking': 2},
    {'name': 'England', 'country': 'England', 'ranking': 3},
    {'name': 'New Zealand', 'country': 'New Zealand', 'ranking': 4},
    {'name': 'Pakistan', 'country': 'Pakistan', 'ranking': 5},
    {'name': 'South Africa', 'country': 'South Africa', 'ranking': 6},
    {'name': 'Bangladesh', 'country': 'Bangladesh', 'ranking': 7},
    {'name': 'West Indies', 'country': 'West Indies', 'ranking': 8},
]

PLAYER_TYPES = ['batsman', 'bowler', 'all-rounder', 'wicket-keeper']
PLAYERS_PER_TEAM = {
    'batsman': 5,
    'bowler': 5,
    'all-rounder': 3,
    'wicket-keeper': 2
}

VENUES = [
    {
        'name': 'Eden Gardens',
        'city': 'Kolkata',
        'country': 'India',
        'capacity': 66000,
        'pitch_type': 'balanced'
    },
    {
        'name': 'MCG',
        'city': 'Melbourne',
        'country': 'Australia',
        'capacity': 100024,
        'pitch_type': 'batting'
    },
    {
        'name': 'Lord\'s',
        'city': 'London',
        'country': 'England',
        'capacity': 30000,
        'pitch_type': 'bowling'
    },
    {
        'name': 'Wankhede Stadium',
        'city': 'Mumbai',
        'country': 'India',
        'capacity': 33108,
        'pitch_type': 'batting'
    }
]

# Credit Range Configuration
CREDIT_RANGES = {
    'batsman': (7.5, 10.5),
    'bowler': (7.5, 10.5),
    'all-rounder': (8.0, 11.0),
    'wicket-keeper': (7.0, 10.0)
}

# Form Factor Configuration
FORM_RANGES = {
    'batsman': (-1.0, 1.0),
    'bowler': (-1.0, 1.0),
    'all-rounder': (-1.0, 1.0),
    'wicket-keeper': (-1.0, 1.0)
}

# Database Configuration
DATABASE_URL = "sqlite:///dream11_prediction.db"  # Update as needed
