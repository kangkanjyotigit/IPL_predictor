import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dream11_prediction.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys (replace with your actual API keys)
    CRICKET_API_KEY = os.environ.get('CRICKET_API_KEY')
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Application configuration
    MATCHES_FETCH_DAYS = 7  # Number of days to fetch upcoming matches
    MAX_PREDICTIONS_PER_USER = 5  # Maximum number of predictions a user can make per match
