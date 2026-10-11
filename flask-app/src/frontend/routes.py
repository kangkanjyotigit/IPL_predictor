"""Frontend routes for Dream11 Prediction"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, current_app, abort, Markup
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import uuid
import random
import logging
from collections import defaultdict
from functools import wraps
import traceback
import inspect
from src.services.team_generator import generate_auto_team, TeamGenerator

from src.database import db
from src.models.user import User
from src.models.match import Match
from src.models.venue import Venue
from src.models.team import Team, TeamPlayer
from src.models.player import Player, PlayerPerformance
from src.utils.constants import PlayerRoles, TeamStrategies, CaptainPreferences
from src.frontend.forms import (
    LoginForm, RegisterForm, ProfileForm, MatchFilterForm, 
    TeamBuilderForm, AutoGenerateTeamForm, VenueForm
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Blueprint from __init__
from . import frontend_bp

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('frontend.index'))
        return f(*args, **kwargs)
    return decorated_function

# Custom error handlers
@frontend_bp.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@frontend_bp.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Error handlers
@frontend_bp.route('/')
def index():
    """Render the home page"""
    try:
        # Get matches
        upcoming_matches = Match.query.filter_by(status='upcoming').order_by(Match.date).limit(5).all()
        live_matches = Match.query.filter_by(status='live').all()
        
        # Get top players
        top_players = Player.query.order_by(Player.current_form.desc()).limit(5).all()
        
        return render_template('index.html', 
                             upcoming_matches=upcoming_matches,
                             live_matches=live_matches,
                             top_players=top_players)
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', 
                             upcoming_matches=[],
                             live_matches=[],
                             top_players=[])

@frontend_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # Get next parameter for redirection after login
    next_page = request.args.get('next')
    logger.info(f"Login route accessed. Next page: {next_page}")
    
    # Check for force_logout parameter for debugging
    force_logout = request.args.get('force_logout', '0') == '1'
    
    if force_logout and current_user.is_authenticated:
        logger.info(f"Force logout requested for user: {current_user.username} (ID: {current_user.id})")
        logout_user()
        session.clear()
        flash('You have been logged out to allow a new login.', 'info')
    # Check if user is already logged in and not forcing logout
    elif current_user.is_authenticated and not force_logout:
        logger.info(f"User already authenticated as {current_user.username} (ID: {current_user.id})")
        if next_page:
            logger.info(f"Redirecting authenticated user to: {next_page}")
            return redirect(next_page)
        return redirect(url_for('frontend.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            username = form.username.data
            password = form.password.data
            logger.info(f"Login attempt for username: {username}")
            
            # Debug: Check if user exists
            all_users = User.query.all()
            logger.info(f"All users in database: {[(u.id, u.username, u.email) for u in all_users]}")
            
            user = User.query.filter_by(username=username).first()
            
            if user:
                logger.info(f"User found: {user.id}, username: {user.username}")
                logger.info(f"User password hash: {user.password_hash[:10]}...")
                password_match = user.check_password(password)
                logger.info(f"Password match: {password_match}")
                
                if password_match:
                    # Use Flask-Login to log in the user with remember=True for persistent sessions
                    login_user(user, remember=True)
                    logger.info(f"Login successful for user: {user.id}")
                    
                    # Set session data
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['is_authenticated'] = True
                    session.permanent = True
                    
                    # Debug session
                    logger.info(f"Session data after login: {dict(session)}")
                    logger.info(f"Is authenticated after login: {current_user.is_authenticated}")
                    
                    # Update last login time
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                    
                    flash('Successfully logged in!', 'success')
                    
                    # Redirect to next page if specified
                    next_page = request.args.get('next')
                    if next_page:
                        logger.info(f"Redirecting to next page: {next_page}")
                        return redirect(next_page)
                    logger.info("Redirecting to dashboard")
                    return redirect(url_for('frontend.dashboard'))
                else:
                    logger.warning(f"Invalid password for user: {username}")
            else:
                logger.warning(f"User not found: {username}")
            
            flash('Invalid username or password', 'danger')
            logger.warning(f"Failed login attempt for username: {username}")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')
    else:
        # Log form validation errors
        if form.errors:
            logger.error(f"Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')
    
    return render_template('login.html', form=form)

@frontend_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('frontend.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            logger.info(f"Registration attempt for username: {form.username.data}")
            
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already exists', 'danger')
                return render_template('register.html', form=form)
            
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered', 'danger')
                return render_template('register.html', form=form)
            
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User registered successfully: {user.id}")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('frontend.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
    else:
        # Log form validation errors
        if form.errors:
            logger.error(f"Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')
    
    return render_template('register.html', form=form)

@frontend_bp.route('/logout')
def logout():
    """Handle user logout"""
    try:
        # Log the logout attempt
        if current_user.is_authenticated:
            logger.info(f"Logout for user: {current_user.username} (ID: {current_user.id})")
        
        # Use Flask-Login's logout_user function
        logout_user()
        
        # Clear all session data
        session.clear()
        
        # Create response with redirect
        response = redirect(url_for('frontend.index'))
        
        # Clear Flask-Login remember cookie
        response.delete_cookie('remember_token')
        
        # Clear session cookie
        response.delete_cookie('session')
        
        # Log successful logout
        logger.info("User successfully logged out and session cleared")
        
        flash('Successfully logged out!', 'success')
        return response
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        flash('An error occurred during logout. Please try again.', 'danger')
        return redirect(url_for('frontend.index'))

@frontend_bp.route('/dashboard')
@login_required
def dashboard():
    """Render user dashboard"""
    try:
        # Use current_user from Flask-Login instead of manually accessing session
        user = current_user
        
        # Get user's teams with match information
        teams = db.session.query(Team).filter_by(user_id=user.id).join(Team.match).order_by(Team.created_at.desc()).all()
        
        # Get upcoming matches
        upcoming_matches = Match.query.filter_by(status='upcoming').order_by(Match.date).limit(5).all()
        
        # Get recent matches
        recent_matches = Match.query.filter_by(status='completed').order_by(Match.date.desc()).limit(5).all()
        
        return render_template('dashboard.html',
                             user=user,
                             teams=teams,
                             upcoming_matches=upcoming_matches,
                             recent_matches=recent_matches)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('An error occurred while loading the dashboard.', 'danger')
        return redirect(url_for('frontend.index'))

@frontend_bp.route('/matches')
def matches():
    """Render matches page"""
    try:
        # Get matches with filter options
        status_filter = request.args.get('status', 'all')
        
        if status_filter == 'all':
            matches = Match.query.order_by(Match.date.desc()).all()
        else:
            matches = Match.query.filter_by(status=status_filter).order_by(Match.date.desc()).all()
        
        return render_template('matches.html', matches=matches, current_filter=status_filter)
    except Exception as e:
        logger.error(f"Matches page error: {str(e)}")
        flash('An error occurred while loading matches.', 'danger')
        return redirect(url_for('frontend.index'))

@frontend_bp.route('/match/<int:match_id>')
def match_detail(match_id):
    """Ultra-robust match detail page that works in all circumstances"""
    try:
        # First check if database is accessible
        try:
            # Check if the Match table exists
            db.session.query(Match).limit(1).all()
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            # Handle missing database by creating emergency data
            return emergency_match_response(match_id)
            
        # Get the match with proper error handling
        match = Match.query.get(match_id)
        if not match:
            logger.warning(f"Match with ID {match_id} not found, creating emergency match")
            # Create an emergency match object if not found
            match = create_emergency_match(match_id)
            
        logger.info(f"Accessing match detail for match {match_id}: {match.team1} vs {match.team2}")
        
        # Get teams for this match with robust error handling
        user_teams = []
        if current_user.is_authenticated:
            try:
                user_teams = Team.query.filter_by(user_id=current_user.id, match_id=match.id).all()
            except Exception as team_error:
                logger.warning(f"Error loading teams: {str(team_error)}")
        
        # Load basic player data with very robust error handling
        basic_team1_players = []
        basic_team2_players = []
        try:
            # Try to get players for team 1
            basic_team1_players = Player.query.filter_by(team_name=match.team1).all()
            if not basic_team1_players:
                # Create emergency players if none found
                basic_team1_players = create_emergency_players(match.team1)
                
            # Try to get players for team 2
            basic_team2_players = Player.query.filter_by(team_name=match.team2).all()
            if not basic_team2_players:
                # Create emergency players if none found
                basic_team2_players = create_emergency_players(match.team2)
                
        except Exception as player_error:
            logger.warning(f"Error loading player data: {str(player_error)}")
            # Create emergency players on exception
            basic_team1_players = create_emergency_players(match.team1)
            basic_team2_players = create_emergency_players(match.team2)
        
        # Add venue information with robust error handling
        venue_name = "Unknown Venue"
        venue_city = "Unknown City"
        try:
            if hasattr(match, 'venue') and match.venue:
                venue_name = match.venue.name
                venue_city = match.venue.city
        except Exception as venue_error:
            logger.warning(f"Error loading venue: {str(venue_error)}")
        
        # Return the template with all needed data
        return render_template('match_detail.html', 
                              match=match, 
                              teams=user_teams,
                              team1_players=basic_team1_players,
                              team2_players=basic_team2_players,
                              venue_name=venue_name,
                              venue_city=venue_city,
                              use_async_loading=True)
    except Exception as e:
        logger.error(f"Unhandled error in match_detail: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Handle any possible error with emergency response
        return emergency_match_response(match_id)

def create_emergency_match(match_id):
    """Create an emergency match object that won't be saved to DB"""
    try:
        # Try to save emergency match to database
        match = Match(
            id=match_id,
            team1="Team A",
            team2="Team B",
            date=datetime.now(),
            status="upcoming",
            format="T20",
            series_name="Emergency Series"
        )
        db.session.add(match)
        db.session.commit()
        logger.info(f"Created emergency match with ID {match_id} in database")
        return match
    except Exception as e:
        logger.warning(f"Could not create emergency match in DB: {str(e)}")
        # Create a transient object not connected to the session
        from datetime import datetime
        class EmergencyMatch:
            def __init__(self, match_id):
                self.id = match_id
                self.team1 = "Team A"
                self.team2 = "Team B"
                self.date = datetime.now()
                self.status = "upcoming"
                self.format = "T20"
                self.series_name = "Emergency Series"
                self.result = None
                self.external_id = f"EMERGENCY_{match_id}"
                
        return EmergencyMatch(match_id)

def create_emergency_players(team_name, count=15):
    """Create emergency players with a balanced distribution of roles suitable for Dream11
    
    Ensures we have enough of each player type for a valid team:
    - 4-6 Batsman
    - 3-5 Bowlers
    - 2-4 All-Rounders
    - 1-2 Wicket-Keepers
    """
    # Generate a balanced set of players with proper role distribution
    roles_distribution = {
        "Batsman": 5,         # 5 batsmen
        "Bowler": 4,          # 4 bowlers
        "All-Rounder": 4,     # 4 all-rounders
        "Wicket-Keeper": 2,   # 2 wicket-keepers
    }
    
    players = []
    
    try:
        # Try to save emergency players to database
        player_idx = 1
        for role, count in roles_distribution.items():
            for i in range(count):
                # Vary credits slightly to make players unique
                credit = round(7.5 + (random.random() * 3), 1)  # Credits between 7.5 and 10.5
                form = round(0.6 + (random.random() * 0.4), 2)  # Form between 0.6 and 1.0
                
                player = Player(
                    name=f"{team_name}_{role[:3]}{player_idx}",
                    team_name=team_name,
                    role=role,
                    credit_value=credit,
                    current_form=form
                )
                db.session.add(player)
                players.append(player)
                player_idx += 1
                
        db.session.commit()
        logger.info(f"Created {len(players)} emergency players for {team_name} in database")
    except Exception as e:
        logger.warning(f"Could not create emergency players in DB: {str(e)}")
        # Create transient objects not connected to the session
        class EmergencyPlayer:
            def __init__(self, name, team, role, credit=8.5, form=0.75):
                self.name = name
                self.team_name = team
                self.role = role
                self.credit_value = credit
                self.current_form = form
                
        players = []
        player_idx = 1
        for role, count in roles_distribution.items():
            for i in range(count):
                # Vary credits slightly to make players unique
                credit = round(7.5 + (random.random() * 3), 1)  # Credits between 7.5 and 10.5
                form = round(0.6 + (random.random() * 0.4), 2)  # Form between 0.6 and 1.0
                
                players.append(EmergencyPlayer(
                    f"{team_name}_{role[:3]}{player_idx}", 
                    team_name, 
                    role,
                    credit,
                    form
                ))
                player_idx += 1
            
    return players

def emergency_match_response(match_id):
    """Generate a modern, well-styled emergency response"""
    # Create emergency data
    match = create_emergency_match(match_id)
    team1_players = create_emergency_players(match.team1)
    team2_players = create_emergency_players(match.team2)
    
    # Skip the template rendering entirely and return a complete HTML response
    # This avoids any issues with template inheritance or static file loading
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{match.team1} vs {match.team2} | Dream11 Prediction</title>
        
        <!-- Bootstrap 4 CSS direct CDN link -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
        <!-- Font Awesome direct CDN link -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        
        <style>
            body {{ 
                background-color: #f0f8ff; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #333;
                line-height: 1.6;
            }}
            
            .navbar {{ 
                background: linear-gradient(to right, #1976d2, #2196f3);
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 12px 0;
            }}
            
            .navbar-brand {{ 
                color: white;
                font-weight: 700;
                font-size: 1.4rem;
            }}
            
            .navbar .nav-link {{ 
                color: rgba(255,255,255,0.85);
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 4px;
                transition: all 0.3s ease;
            }}
            
            .navbar .nav-link:hover {{ 
                background-color: rgba(255,255,255,0.15);
                color: white;
            }}
            
            .match-header {{ 
                background: linear-gradient(45deg, #2196f3, #03a9f4);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            
            .team-container {{ 
                text-align: center;
                padding: 15px;
            }}
            
            .team-logo {{ 
                width: 80px;
                height: 80px;
                background-color: rgba(255,255,255,0.2);
                border-radius: 50%;
                margin: 0 auto 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: bold;
            }}
            
            .vs-badge {{ 
                background-color: rgba(255,255,255,0.2);
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 20px;
                margin: 15px 0;
            }}
            
            .match-info {{ 
                text-align: center;
                margin-top: 20px;
                padding: 15px;
                background-color: rgba(255,255,255,0.1);
                border-radius: 10px;
            }}
            
            .card {{ 
                border: none;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                margin-bottom: 24px;
            }}
            
            .card:hover {{ 
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }}
            
            .card-header {{ 
                background-color: #f7f9fc;
                border-bottom: 1px solid #edf2f7;
                font-weight: 600;
                padding: 15px 20px;
            }}
            
            .status-badge {{ 
                padding: 8px 15px;
                border-radius: 20px;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 14px;
                letter-spacing: 0.5px;
            }}
            
            .status-upcoming {{ 
                background-color: #4caf50;
                color: white;
            }}
            
            footer {{ 
                background-color: #f1f1f1;
                color: #333;
                padding: 30px 0;
                margin-top: 50px;
            }}
            
            .player-role {{ 
                display: inline-block;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 0.8rem;
                margin-top: 10px;
            }}
            
            .role-Batsman {{ 
                background-color: #e3f2fd;
                color: #0d47a1;
            }}
            
            .role-Bowler {{ 
                background-color: #e8f5e9;
                color: #1b5e20;
            }}
            
            .role-All-Rounder {{ 
                background-color: #fff3e0;
                color: #e65100;
            }}
            
            .role-Wicket-Keeper {{ 
                background-color: #f3e5f5;
                color: #4a148c;
            }}
        </style>
    </head>
        <body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="{url_for('frontend.index')}">Dream11 Prediction</a>
            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ml-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{url_for('frontend.index')}">Home</a>
                    </li>
                    <li class="nav-item active">
                        <a class="nav-link" href="{url_for('frontend.matches')}">Matches</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main content -->
    <main>
        <div class="container mt-4 mb-4">
            <div class="row">
                <div class="col-md-12">
                    <nav aria-label="breadcrumb">
                        <ol class="breadcrumb">
                            <li class="breadcrumb-item"><a href="{url_for('frontend.index')}">Home</a></li>
                            <li class="breadcrumb-item"><a href="{url_for('frontend.matches')}">Matches</a></li>
                            <li class="breadcrumb-item active">{match.team1} vs {match.team2}</li>
                        </ol>
                    </nav>
                </div>
            </div>
            
            <div class="alert alert-warning mb-4">
                <i class="fas fa-exclamation-circle mr-2"></i>
                <strong>Emergency Mode:</strong> Using sample data while API data is unavailable.
            </div>
            
            <!-- Generate Team Button --> 
            <div class="row mb-4">
                <div class="col-md-12 text-center">
                    <a href="{url_for('frontend.auto_generate_team', match_id=match.id)}" class="btn btn-primary btn-lg" style="background: linear-gradient(45deg, #1976d2, #03a9f3); border: none; padding: 12px 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                        <i class="fas fa-magic mr-2"></i> Generate Fantasy Team
                    </a>
                    <p class="mt-2 text-muted">Optimize your Dream11 team based on player performance and analytics</p>
                </div>
            </div>
            
            <div class="match-header">
                <div class="row align-items-center">
                    <div class="col-md-4">
                        <div class="team-container">
                            <div class="team-logo">{match.team1[:2]}</div>
                            <h3>{match.team1}</h3>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="vs-badge">VS</div>
                        <div class="mt-3">
                            <span class="status-badge status-{match.status}">{match.status.upper()}</span>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="team-container">
                            <div class="team-logo">{match.team2[:2]}</div>
                            <h3>{match.team2}</h3>
                        </div>
                    </div>
                </div>
                
                <div class="match-info mt-4">
                    <div><i class="fas fa-trophy"></i> {match.format} | {match.series_name}</div>
                    <div class="mt-2"><i class="fas fa-calendar-alt"></i> {match.date.strftime('%d %b %Y, %H:%M')}</div>
                    <div class="mt-2"><i class="fas fa-map-marker-alt"></i> Emirates Cricket Stadium, Dubai</div>
                </div>
            </div>
                    
                    <!-- Player comparison -->
                    <div class="row mb-4">
                        <div class="col-md-12">
                            <div class="card">
                                <div class="card-header bg-primary text-white">
                                    <h4>Player Comparison</h4>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <h5 class="text-center mb-3">{match.team1} Players</h5>
                                            <div class="list-group">
                                                {' '.join([f'<div class="list-group-item"><strong>{p.name}</strong> - {p.role}</div>' for p in team1_players[:5]])}
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <h5 class="text-center mb-3">{match.team2} Players</h5>
                                            <div class="list-group">
                                                {' '.join([f'<div class="list-group-item"><strong>{p.name}</strong> - {p.role}</div>' for p in team2_players[:5]])}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Actions -->
                    <div class="row">
                        <div class="col-md-12 text-center">
                            <a href="{url_for('frontend.matches')}" class="btn btn-primary"><i class="fas fa-arrow-left"></i> Back to Matches</a>
                        </div>
                    </div>
                </div>
            </main>

            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer>
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5>Dream11 Prediction</h5>
                    <p>AI-powered cricket prediction and team generation</p>
                </div>
                <div class="col-md-6 text-md-right">
                    <p>&copy; 2025 Dream11 Prediction</p>
                </div>
            </div>
        </div>
    </footer>

    <!-- Scripts -->
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    return html

@frontend_bp.route('/match/<int:match_id>/analytics')
def match_analytics(match_id):
    """API endpoint to get AI-powered match analytics asynchronously"""
    try:
        # Get the match with proper error handling
        match = Match.query.get(match_id)
        if not match:
            logger.error(f"Match with ID {match_id} not found in analytics endpoint")
            return jsonify({"error": "Match not found"}), 404
            
        logger.info(f"Loading analytics for match {match_id}: {match.team1} vs {match.team2}")
        
        # Get players from both teams for analytics with error handling
        try:
            team1_players = Player.query.filter_by(team_name=match.team1).all()
            team2_players = Player.query.filter_by(team_name=match.team2).all()
        except Exception as player_error:
            logger.warning(f"Error loading player data for analytics: {str(player_error)}")
            team1_players = []
            team2_players = []

        # Generate default match insights
        match_insights = {
            'summary': f"Based on our analysis, we predict a competitive match between {match.team1} and {match.team2}.",
            'avg_fantasy_points_team1': 50,
            'avg_fantasy_points_team2': 50,
            'expected_total_score': '150-160',
            'team1_win_probability': 55,
            'team2_win_probability': 45
        }
        
        # Generate default strategy recommendation
        strategy_recommendation = {
            'description': 'Balance your team between both sides',
            'batsmen': '3-4',
            'bowlers': '3-4',
            'all_rounders': '2-3',
            'wicket_keepers': '1-2',
            'captain_strategy': 'Choose best performing player',
            'vice_captain_strategy': 'Choose second best performing player'
        }
        
        # Generate placeholder top players
        top_players = []
        if team1_players and team2_players:
            all_players = team1_players + team2_players
            for player in all_players[:10]:  # Take up to 10 players
                try:
                    credit_value = 8.5
                    if hasattr(player, 'credit_value'):
                        credit_value = player.credit_value
                    
                    current_form = 0
                    if hasattr(player, 'current_form'):
                        current_form = player.current_form
                    
                    player_data = {
                        'name': player.name,
                        'team_name': player.team_name,
                        'role': player.role,
                        'credits': credit_value,
                        'predicted_points': 50 + (current_form * 10),
                        'prediction_explanation': "Performance prediction based on recent form and matchup"
                    }
                    top_players.append(player_data)
                except Exception as player_error:
                    logger.warning(f"Error processing player {player.name}: {str(player_error)}")
            
            # Sort players by predicted points
            if top_players:
                top_players = sorted(top_players, key=lambda x: x['predicted_points'], reverse=True)[:10]
        
        # Return JSON response with analytics data
        response = {
            'match_insights': match_insights,
            'strategy_recommendation': strategy_recommendation,
            'top_players': top_players
        }
        return jsonify(response)
            
    except Exception as e:
        logger.error(f"Unexpected error in match analytics: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'An unexpected error occurred while generating match analytics',
            'match_insights': {
                'summary': 'Data currently unavailable',
                'team1_win_probability': 50,
                'team2_win_probability': 50
            },
            'strategy_recommendation': {
                'description': 'Strategy recommendations not available at this time',
                'batsmen': '3-4',
                'bowlers': '3-4',
                'all_rounders': '2-3',
                'wicket_keepers': '1-2',
                'captain_strategy': 'Choose best performing player',
                'vice_captain_strategy': 'Choose second best performing player'
            },
            'top_players': []
        }), 500

@frontend_bp.route('/players')
def players():
    """Render players page"""
    try:
        # Get players with filter options
        role_filter = request.args.get('role', 'all')
        team_filter = request.args.get('team', 'all')
        
        query = Player.query
        
        if role_filter != 'all':
            query = query.filter_by(role=role_filter)
        
        if team_filter != 'all':
            query = query.filter_by(team_name=team_filter)
        
        players = query.order_by(Player.current_form.desc()).all()
        
        # Get unique team names for filter dropdown
        team_names = db.session.query(Player.team_name).distinct().all()
        team_names = [team[0] for team in team_names]
        
        return render_template('players.html', 
                             players=players, 
                             current_role=role_filter, 
                             current_team=team_filter,
                             team_names=team_names)
    except Exception as e:
        logger.error(f"Players page error: {str(e)}")
        flash('An error occurred while loading players.', 'danger')
        return redirect(url_for('frontend.index'))

@frontend_bp.route('/player/<int:player_id>')
def player_detail(player_id):
    """Render player detail page"""
    try:
        player = Player.query.get_or_404(player_id)
        
        # Get recent performances
        performances = PlayerPerformance.query.filter_by(player_id=player.id).order_by(PlayerPerformance.match_date.desc()).limit(5).all()
        
        return render_template('player_detail.html', player=player, performances=performances)
    except Exception as e:
        logger.error(f"Player detail error: {str(e)}")
        flash('An error occurred while loading player details.', 'danger')
        return redirect(url_for('frontend.players'))

@frontend_bp.route('/venues')
def venues():
    """Render venues page"""
    try:
        venues = Venue.query.all()
        return render_template('venues.html', venues=venues)
    except Exception as e:
        logger.error(f"Venues page error: {str(e)}")
        flash('An error occurred while loading venues.', 'danger')
        return redirect(url_for('frontend.index'))

@frontend_bp.route('/venue/<int:venue_id>')
def venue_detail(venue_id):
    """Render venue detail page"""
    try:
        venue = Venue.query.get_or_404(venue_id)
        
        # Get recent matches at this venue
        recent_matches = Match.query.filter_by(venue_id=venue.id).order_by(Match.date.desc()).limit(10).all()
        
        return render_template('venue_detail.html', venue=venue, recent_matches=recent_matches)
    except Exception as e:
        logger.error(f"Venue detail error: {str(e)}")
        flash('An error occurred while loading venue details.', 'danger')
        return redirect(url_for('frontend.venues'))

@frontend_bp.route('/strategy')
def strategy():
    """Render strategy guide page"""
    try:
        return render_template('strategy.html')
    except Exception as e:
        logger.error(f"Strategy page error: {str(e)}")
        flash('An error occurred while loading the strategy guide.', 'danger')
        return redirect(url_for('frontend.index'))

@frontend_bp.route('/analytics')
@login_required
def analytics():
    """Render analytics page"""
    try:
        user = User.query.get_or_404(session['user_id'])
        
        # Get user's teams
        teams = Team.query.filter_by(user_id=user.id).all()
        
        # Calculate stats
        stats = {
            'total_teams': len(teams),
            'matches_played': 0,
            'total_points': 0,
            'rank': user.rank,
            'prediction_accuracy': user.prediction_accuracy * 100 if user.prediction_accuracy else 0,
            'recent_performance': []
        }
        
        # Get recent team performances
        for team in teams:
            if team.match.status == 'completed':
                stats['matches_played'] += 1
                stats['total_points'] += team.points
                
                # Add to recent performances
                if len(stats['recent_performance']) < 5:
                    stats['recent_performance'].append({
                        'match': team.match,
                        'points': team.points,
                        'rank': team.rank
                    })
        
        # Get top players
        top_players = Player.query.order_by(Player.current_form.desc()).limit(10).all()
        
        return render_template('analytics.html', stats=stats, top_players=top_players)
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        flash('An error occurred while loading analytics.', 'danger')
        return redirect(url_for('frontend.dashboard'))

@frontend_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Render user profile"""
    try:
        user = current_user
        
        form = ProfileForm(obj=user)
        
        if form.validate_on_submit():
            # Check if email is already taken by another user
            if form.email.data != user.email and User.query.filter_by(email=form.email.data).first():
                flash('Email already in use by another account', 'danger')
            else:
                # Update user profile
                form.populate_obj(user)
                db.session.commit()
                flash('Profile updated successfully', 'success')
                return redirect(url_for('frontend.profile'))
        
        return render_template('profile.html', user=user, form=form)
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        flash('An error occurred while loading your profile.', 'danger')
        return redirect(url_for('frontend.dashboard'))

@frontend_bp.route('/team-builder/<int:match_id>', methods=['GET', 'POST'])
@login_required
def team_builder(match_id):
    """Render team builder page"""
    try:
        match = Match.query.get_or_404(match_id)
        
        # Check if match is upcoming
        if match.status != 'upcoming':
            flash('Teams can only be created for upcoming matches', 'warning')
            return redirect(url_for('frontend.match_detail', match_id=match.id))
        
        # Get players from both teams
        team1_players = Player.query.filter_by(team_name=match.team1).all()
        team2_players = Player.query.filter_by(team_name=match.team2).all()
        
        if request.method == 'POST':
            # Process team creation
            team_name = request.form.get('team_name')
            player_ids = request.form.getlist('player_ids')
            captain_id = request.form.get('captain_id')
            vice_captain_id = request.form.get('vice_captain_id')
            
            # Validate team
            if len(player_ids) != 11:
                flash('You must select exactly 11 players', 'danger')
                return render_template('team_builder.html', 
                                     match=match, 
                                     team1_players=team1_players, 
                                     team2_players=team2_players)
            
            # Create team
            team = Team(
                name=team_name,
                user_id=current_user.id,
                match_id=match.id,
                captain_id=captain_id,
                vice_captain_id=vice_captain_id
            )
            db.session.add(team)
            db.session.flush()  # Get team ID
            
            # Add players to team
            for player_id in player_ids:
                team_player = TeamPlayer(team_id=team.id, player_id=player_id)
                db.session.add(team_player)
            
            db.session.commit()
            flash('Team created successfully!', 'success')
            return redirect(url_for('frontend.dashboard'))
        
        return render_template('team_builder.html', 
                             match=match, 
                             team1_players=team1_players, 
                             team2_players=team2_players)
    except Exception as e:
        logger.error(f"Team builder error: {str(e)}")
        flash('An error occurred while loading the team builder.', 'danger')
        return redirect(url_for('frontend.matches'))

@frontend_bp.route('/match/<int:match_id>/auto-generate-team', methods=['GET', 'POST'])
@login_required
def auto_generate_team(match_id):
    """Auto-generate a team for a match"""
    try:
        logger.info(f"Auto-generate team accessed by user: {current_user.id}, match_id: {match_id}")
        logger.info(f"Is authenticated: {current_user.is_authenticated}")
        logger.info(f"Current session data: {dict(session)}")
        
        # Get match details
        try:
            match_id = int(match_id)  # Ensure match_id is an integer
            match = Match.query.get(match_id)
            if not match:
                logger.error(f"Match with ID {match_id} not found")
                flash(f'Match with ID {match_id} not found', 'danger')
                return redirect(url_for('frontend.matches'))
                
            logger.info(f"Match found: {match.id}, {match.team1} vs {match.team2}")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid match_id: {str(e)}")
            flash('Invalid match ID', 'danger')
            return redirect(url_for('frontend.matches'))
        
        # Check if match is upcoming
        if match.status != 'upcoming':
            logger.warning(f"Match {match_id} is not upcoming, status: {match.status}")
            flash('Teams can only be created for upcoming matches', 'warning')
            return redirect(url_for('frontend.match_detail', match_id=match.id))
            
        # Load and ensure enough players for both teams; generate emergency players if needed
        team1_players = Player.query.filter_by(team_name=match.team1).all()
        if len(team1_players) < 11:
            logger.warning(f"Insufficient players for team {match.team1} (found {len(team1_players)}), generating emergency players.")
            create_emergency_players(match.team1)
            team1_players = Player.query.filter_by(team_name=match.team1).all()

        team2_players = Player.query.filter_by(team_name=match.team2).all()
        if len(team2_players) < 11:
            logger.warning(f"Insufficient players for team {match.team2} (found {len(team2_players)}), generating emergency players.")
            create_emergency_players(match.team2)
            team2_players = Player.query.filter_by(team_name=match.team2).all()

        logger.info(f"Found {len(team1_players)} players for {match.team1} and {len(team2_players)} players for {match.team2}")
        
        # Initialize form
        form = AutoGenerateTeamForm()
        
        if request.method == 'POST':
            logger.info(f"POST request received for auto-generate team")
            logger.info(f"Form data: {request.form}")
            
            # Check if CSRF token is valid
            logger.info(f"CSRF token from form: {form.csrf_token.current_token}")
            logger.info(f"CSRF token from session: {session.get('_csrf_token')}")
            
            logger.info(f"Form validation: {form.validate_on_submit()}")
            
            if form.errors:
                logger.warning(f"Form validation errors: {form.errors}")
                
                # Display specific error messages for each field
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"Error in {field}: {error}", "danger")
                        
                # Log detailed information for debugging
                logger.debug(f"Form data submitted: {request.form}")
                logger.debug(f"Available captain preferences: {[choice[0] for choice in CaptainPreferences.CAPTAIN_CHOICES]}")
                logger.debug(f"Available vice-captain preferences: {[choice[0] for choice in CaptainPreferences.VICE_CAPTAIN_CHOICES]}")
            
            if form.validate_on_submit():
                try:
                    # Generate team name if not provided
                    team_name = form.team_name.data
                    if not team_name or team_name.strip() == "":
                        team_name = f"Auto Team - {match.team1} vs {match.team2}"
                    
                    # Log the team generation attempt
                    logger.info(f"Auto-generating team for user {current_user.id}, match {match_id}, strategy: {form.strategy.data}")
                    
                    # Prepare parameters with explicit type conversion and validation
                    # These parameters must match exactly what TeamGenerator expects
                    
                    # Validate captain preference
                    captain_pref = str(form.captain_preference.data)
                    valid_captain_prefs = [choice[0] for choice in CaptainPreferences.CAPTAIN_CHOICES]
                    if captain_pref not in valid_captain_prefs:
                        logger.warning(f"Invalid captain preference: {captain_pref}, using default")
                        captain_pref = CaptainPreferences.HIGHEST_POINTS
                    
                    # Validate vice captain preference
                    vice_captain_pref = str(form.vice_captain_preference.data)
                    valid_vice_captain_prefs = [choice[0] for choice in CaptainPreferences.VICE_CAPTAIN_CHOICES]
                    if vice_captain_pref not in valid_vice_captain_prefs:
                        logger.warning(f"Invalid vice captain preference: {vice_captain_pref}, using default")
                        vice_captain_pref = CaptainPreferences.SECOND_HIGHEST_POINTS
                    
                    generation_params = {
                        'match_id': match_id,
                        'user_id': current_user.id,
                        'db': db,
                        'team_name': team_name,
                        'strategy': str(form.strategy.data),
                        'max_players_from_team': int(form.max_players_from_team.data),
                        'form_weight': float(form.form_weight.data),
                        'credit_weight': float(form.credit_weight.data),
                        'captain_preference': captain_pref,
                        'vice_captain_preference': vice_captain_pref,
                        'consider_opposition': bool(form.consider_opposition.data),
                        'apply_budget_optimization': bool(form.apply_budget_optimization.data)
                    }
                    
                    # Log generation parameters
                    logger.info(f"Team generation parameters: {generation_params}")
                    
                    # Log parameters before generation
                    logger.info(f"Calling generate_auto_team with parameters:")
                    for key, value in generation_params.items():
                        logger.info(f"  {key}: {value} (type: {type(value)})")
                    
                    # Generate team using explicit unpacking of parameters
                    try:
                        # The generate_auto_team function now returns a tuple (team, error_message)
                        team_with_players, error_message = generate_auto_team(**generation_params)
                        
                        # Log the result
                        logger.info(f"generate_auto_team returned team: {team_with_players}, error: {error_message}")
                        
                        if error_message:
                            logger.error(f"Team generation error: {error_message}")
                            
                            # Format error message for user display with enhanced details
                            user_friendly_error = error_message
                            
                            # Make specific error messages more user-friendly with detailed suggestions
                            if "Not enough" in error_message and "players available" in error_message:
                                user_friendly_error = Markup(f"""<strong>Team Generation Failed:</strong> {error_message}. 
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Check that both teams have enough players in each role (batsmen, bowlers, all-rounders, wicket-keepers)</li>
                                    <li>Try a different strategy that requires fewer players of a specific role</li>
                                    <li>Add more players to the database for both teams</li>
                                </ul>""")
                            elif "Insufficient players for required roles" in error_message:
                                user_friendly_error = Markup(f"""<strong>Team Generation Failed:</strong> {error_message}. 
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Add more players with the missing roles to the database</li>
                                    <li>Try a different strategy that requires fewer players of the missing roles</li>
                                </ul>""")
                            elif "Unable to create a valid team with exactly 11 players" in error_message or "Failed to select exactly 11 players" in error_message:
                                user_friendly_error = Markup(f"""<strong>Team Generation Failed:</strong> Could not create a valid team with the current constraints. 
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Increase the maximum players allowed from a single team (currently {form.max_players_from_team.data})</li>
                                    <li>Try a different strategy like 'balanced' or 'all_rounders'</li>
                                    <li>Adjust the form and credit weights to allow for more player selection flexibility</li>
                                </ul>""")
                            elif "Team exceeds credit limit" in error_message:
                                user_friendly_error = Markup(f"""<strong>Team Generation Failed:</strong> {error_message}. 
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Increase the credit weight parameter (currently {form.credit_weight.data}) to prioritize lower-credit players</li>
                                    <li>Try the 'budget' strategy which focuses on optimizing credits</li>
                                    <li>Set apply_budget_optimization to True</li>
                                </ul>""")
                            elif "Database error" in error_message:
                                user_friendly_error = Markup(f"""<strong>Database Error:</strong> An error occurred while saving the team. 
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Please try again later</li>
                                    <li>If the problem persists, contact the administrator</li>
                                </ul>""")
                            elif "Cannot create a valid team with current constraints" in error_message:
                                user_friendly_error = Markup(f"""<strong>Team Generation Failed:</strong> Could not create a valid team with the current constraints. 
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Increase the maximum players allowed from a single team (currently {form.max_players_from_team.data})</li>
                                    <li>Try a different strategy</li>
                                    <li>Adjust the form weight ({form.form_weight.data}) and credit weight ({form.credit_weight.data})</li>
                                </ul>""")
                            elif "No players were selected" in error_message:
                                user_friendly_error = Markup(f"""<strong>Team Generation Failed:</strong> No players could be selected with the current parameters. 
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Check that players have valid credit points and form values</li>
                                    <li>Try a different strategy</li>
                                    <li>Increase the maximum players from a team</li>
                                </ul>""")
                            elif "Error selecting captain/vice-captain" in error_message:
                                user_friendly_error = Markup(f"""<strong>Team Generation Failed:</strong> Could not select captain and vice-captain. 
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Try a different captain preference (currently {form.captain_preference.data})</li>
                                    <li>Try a different vice-captain preference (currently {form.vice_captain_preference.data})</li>
                                </ul>""")
                            else:
                                user_friendly_error = Markup(f"""<strong>Error generating team:</strong> {error_message}
                                <br><br><strong>Suggestions:</strong>
                                <ul>
                                    <li>Try different parameters</li>
                                    <li>Check the debug page for more details</li>
                                    <li>Try a different match if the problem persists</li>
                                </ul>""")
                                
                            flash(user_friendly_error, 'danger')
                            return redirect(url_for('frontend.match_detail', match_id=match.id))
                            
                    except Exception as gen_error:
                        logger.error(f"Exception in generate_auto_team: {str(gen_error)}")
                        logger.error(traceback.format_exc())
                        db.session.rollback()
                        
                        # Create a user-friendly error message
                        user_friendly_error = Markup(f"<strong>Error generating team:</strong> An unexpected error occurred. Please try again with different parameters.")
                        flash(user_friendly_error, 'danger')
                        return redirect(url_for('frontend.match_detail', match_id=match.id))
                    
                    if team_with_players:
                        logger.info(f"Team generated successfully, team ID: {team_with_players.id}")
                        
                        try:
                            # Get team players
                            team = team_with_players
                            team_players = db.session.query(TeamPlayer, Player).join(
                                Player, TeamPlayer.player_id == Player.id
                            ).filter(TeamPlayer.team_id == team.id).all()
                            
                            if not team_players:
                                logger.error(f"No players found for team ID {team.id}")
                                flash('No players found in the generated team. Please try again.', 'danger')
                                return redirect(url_for('frontend.match_detail', match_id=match.id))
                            
                            logger.info(f"Team players found: {len(team_players)}")
                            
                            # Get captain and vice-captain
                            captain = db.session.query(Player).filter_by(id=team.captain_id).first()
                            vice_captain = db.session.query(Player).filter_by(id=team.vice_captain_id).first()
                            
                            if not captain or not vice_captain:
                                logger.error(f"Captain or vice-captain not found for team ID {team.id}")
                                flash('Error retrieving captain or vice-captain. Please try again.', 'danger')
                                return redirect(url_for('frontend.match_detail', match_id=match.id))
                            
                            logger.info(f"Captain: {captain.name}, Vice-captain: {vice_captain.name}")
                            
                            # Group players by role
                            players_by_role = defaultdict(list)
                            role_counts = {}
                            role_labels = []
                            
                            for tp, player in team_players:
                                normalized_role = PlayerRoles.normalize_role(player.role)
                                players_by_role[normalized_role].append(player)
                                
                                # Count each role for chart data
                                if normalized_role in role_counts:
                                    role_counts[normalized_role] += 1
                                else:
                                    role_counts[normalized_role] = 1
                                    role_labels.append(normalized_role)
                            
                            # Prepare chart data
                            role_count_values = [role_counts[role] for role in role_labels]
                            
                            logger.info(f"Players by role: {[(role, len(players)) for role, players in players_by_role.items()]}")
                            
                            # Calculate team statistics
                            total_credits = sum(player.credit_points for _, player in team_players)
                            avg_form = sum(player.current_form for _, player in team_players) / len(team_players)
                            
                            logger.info(f"Team stats - Total credits: {total_credits}, Avg form: {avg_form}")
                            
                            # Calculate team distribution (players per team)
                            team_distribution = {}
                            for _, player in team_players:
                                if player.team_name in team_distribution:
                                    team_distribution[player.team_name] += 1
                                else:
                                    team_distribution[player.team_name] = 1
                            
                            logger.info(f"Team distribution: {team_distribution}")
                            
                            flash('Team generated successfully!', 'success')
                            return render_template('auto_generate_team.html', 
                                                  match=match,
                                                  form=form,
                                                  team=team_with_players,
                                                  team_players=team_players,
                                                  players_by_role=players_by_role,
                                                  captain=captain,
                                                  vice_captain=vice_captain,
                                                  total_credits=total_credits,
                                                  avg_form=avg_form,
                                                  team_distribution=team_distribution,
                                                  role_labels=role_labels,
                                                  role_counts=role_count_values,
                                                  generated=True)
                        except Exception as e:
                            logger.error(f"Error processing team data: {str(e)}")
                            logger.error(traceback.format_exc())
                            db.session.rollback()
                            flash('Error processing team data. Please try again.', 'danger')
                            return redirect(url_for('frontend.match_detail', match_id=match.id))
                    else:
                        logger.error("Team generation returned None")
                        flash('Failed to generate team. Please try different parameters or use the debug route.', 'danger')
                        # Add a link to the debug route
                        flash(Markup(f'Try the <a href="{url_for("frontend.debug_auto_generate", match_id=match.id)}">debug route</a> for more detailed error information.'), 'info')
                except Exception as e:
                    logger.error(f"Error generating team: {str(e)}")
                    logger.error(traceback.format_exc())
                    db.session.rollback()
                    error_message = str(e)
                    if 'no such table' in error_message.lower():
                        flash('Database error: Tables not properly initialized. Please contact support.', 'danger')
                    elif 'no such column' in error_message.lower():
                        flash('Database error: Column missing. Please contact support.', 'danger')
                    elif 'not enough' in error_message.lower() and 'players' in error_message.lower():
                        flash('Not enough players available to create a team with the current constraints.', 'danger')
                    else:
                        flash(f'An unexpected error occurred: {error_message}', 'danger')
            else:
                # Form validation failed
                logger.warning(f"Form validation failed: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"Error in {field}: {error}", 'danger')
        
        # For GET requests or if form validation fails
        # Get all players for this match
        team1_players = Player.query.filter_by(team_name=match.team1).all()
        team2_players = Player.query.filter_by(team_name=match.team2).all()
        
        # Group players by role for display
        all_players = team1_players + team2_players
        players_by_role = defaultdict(list)
        
        for player in all_players:
            normalized_role = PlayerRoles.normalize_role(player.role)
            players_by_role[normalized_role].append(player)
        
        logger.info(f"Rendering auto_generate_team.html template with generated=False")
        return render_template('auto_generate_team.html',
                              match=match,
                              form=form,
                              team1_players=team1_players,
                              team2_players=team2_players,
                              players_by_role=players_by_role,
                              generated=False)
    except Exception as e:
        logger.error(f"Auto-generate team error: {str(e)}")
        logger.error(traceback.format_exc())
        error_message = str(e)
        if 'no such table' in error_message.lower():
            flash('Database error: Tables not properly initialized. Please contact support.', 'danger')
        elif 'no such column' in error_message.lower():
            flash('Database error: Column missing. Please contact support.', 'danger')
        elif 'not enough' in error_message.lower() and 'players' in error_message.lower():
            flash('Not enough players available to create a team.', 'danger')
        else:
            flash(f'An error occurred while loading the auto-generate team page: {error_message}', 'danger')
        return redirect(url_for('frontend.matches'))

@frontend_bp.route('/debug/auto-generate/<int:match_id>')
@login_required
def debug_auto_generate(match_id):
    """Debug route for auto-generating a team with detailed diagnostics"""
    try:
        # Log request
        logger.info(f"Debug auto-generate accessed by user {current_user.id} for match {match_id}")
        
        # Get match with error handling
        try:
            match_id = int(match_id)  # Ensure match_id is an integer
            match = Match.query.get(match_id)
            if not match:
                error_msg = f"Match with ID {match_id} not found"
                logger.error(error_msg)
                return render_template('debug_error.html',
                                    error=error_msg,
                                    traceback="No match found in database with this ID")
                
            logger.info(f"Match found: {match.id}, {match.team1} vs {match.team2}")
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid match_id: {str(e)}"
            logger.error(error_msg)
            return render_template('debug_error.html',
                                error=error_msg,
                                traceback=traceback.format_exc())
        
        # Load and ensure enough players for both teams; generate emergency players if needed
        team1_players = Player.query.filter_by(team_name=match.team1).all()
        if len(team1_players) < 11:
            logger.warning(f"Insufficient players for team {match.team1} (found {len(team1_players)}), generating emergency players.")
            create_emergency_players(match.team1)
            team1_players = Player.query.filter_by(team_name=match.team1).all()

        team2_players = Player.query.filter_by(team_name=match.team2).all()
        if len(team2_players) < 11:
            logger.warning(f"Insufficient players for team {match.team2} (found {len(team2_players)}), generating emergency players.")
            create_emergency_players(match.team2)
            team2_players = Player.query.filter_by(team_name=match.team2).all()

        logger.info(f"Found {len(team1_players)} players for {match.team1} and {len(team2_players)} players for {match.team2}")
        
        # Check player roles for each team
        team1_roles = {}
        team2_roles = {}
        for player in team1_players:
            role = player.role
            team1_roles[role] = team1_roles.get(role, 0) + 1
        for player in team2_players:
            role = player.role
            team2_roles[role] = team2_roles.get(role, 0) + 1
            
        logger.info(f"Team1 roles: {team1_roles}")
        logger.info(f"Team2 roles: {team2_roles}")
        
        # Create test parameters
        test_params = {
            'match_id': match_id,
            'user_id': current_user.id,
            'db': db,
            'team_name': f"Debug Team - {match.team1} vs {match.team2}",
            'strategy': 'balanced',
            'max_players_from_team': 7,
            'form_weight': 0.6,
            'credit_weight': 0.4,
            'captain_preference': 'highest_points',
            'vice_captain_preference': 'second_highest_points',
            'consider_opposition': True,
            'apply_budget_optimization': True
        }
        
        # Get function signature
        sig = inspect.signature(generate_auto_team)
        params_info = [f"{name}: {param.default}" for name, param in sig.parameters.items()]
        logger.info(f"Function signature: generate_auto_team({', '.join(params_info)})")
        
        # Log parameters for debugging
        logger.info(f"Debug parameters:")
        for key, value in test_params.items():
            if key != 'db':  # Skip db to avoid huge log
                logger.info(f"  {key}: {value} (type: {type(value)})")
                debug_output.append(f"<p><strong>{key}:</strong> {value} (type: {type(value)})</p>")
        
        # Try team generation with explicit parameters and detailed error handling
        debug_output.append(f"<div class='alert alert-info'>Using strategy: {test_params['strategy']}, Max players per team: {test_params['max_players_from_team']}</div>")
        
        try:
            # The generate_auto_team function now returns a tuple (team, error_message)
            team, error_message = generate_auto_team(**test_params)
            
            # Log the result
            logger.info(f"Debug generate_auto_team returned team: {team}, error: {error_message}")
            
            if error_message:
                # Format error message for detailed debugging
                debug_output.append(f"<div class='alert alert-danger'><strong>Error:</strong> {error_message}</div>")
                
                # Add suggestions based on error type
                if "Not enough" in error_message and "players available" in error_message:
                    debug_output.append(f"<div class='alert alert-warning'><strong>Suggestion:</strong> Check that both teams have enough players in each role. Current distribution:<br>")
                    debug_output.append(f"<strong>{match.team1}:</strong> {team1_roles}<br>")
                    debug_output.append(f"<strong>{match.team2}:</strong> {team2_roles}</div>")
                    
                elif "Unable to create a valid team with exactly 11 players" in error_message:
                    debug_output.append(f"<div class='alert alert-warning'><strong>Suggestion:</strong> Try increasing max_players_from_team (currently {test_params['max_players_from_team']})</div>")
                    
                elif "Team exceeds credit limit" in error_message:
                    debug_output.append(f"<div class='alert alert-warning'><strong>Suggestion:</strong> Try adjusting form_weight and credit_weight to prioritize lower credit players</div>")
                    
                elif "Cannot create a valid team with current constraints" in error_message:
                    debug_output.append(f"<div class='alert alert-warning'><strong>Suggestion:</strong> Try relaxing constraints by increasing max_players_from_team or adjusting the strategy</div>")
                
                # Add a section for trying different parameters
                debug_output.append(f"<h4>Try Different Parameters</h4>")
                debug_output.append(f"<p>You can try the following parameter combinations:</p>")
                debug_output.append(f"<ul>")
                debug_output.append(f"<li>Increase max_players_from_team to 8 or 9</li>")
                debug_output.append(f"<li>Try different strategies: 'balanced', 'aggressive', 'conservative'</li>")
                debug_output.append(f"<li>Adjust form_weight to prioritize different player attributes</li>")
                debug_output.append(f"</ul>")
                
                return render_template('debug.html', title='Debug Team Generation', debug_output=debug_output)
                
            if team:
                logger.info(f"Debug team generated successfully with ID: {team.id}")
                
                # Get team details for verification
                team_players = db.session.query(TeamPlayer, Player).join(
                    Player, TeamPlayer.player_id == Player.id
                ).filter(TeamPlayer.team_id == team.id).all()
                
                # Verify we have 11 players
                if len(team_players) != 11:
                    logger.error(f"Team has {len(team_players)} players instead of 11")
                    debug_output.append(f"<div class='alert alert-danger'>Team has {len(team_players)} players instead of 11</div>")
                    return render_template('debug.html', title='Debug Team Generation', debug_output=debug_output)
                
                # Get captain and vice-captain
                captain = db.session.query(Player).filter_by(id=team.captain_id).first()
                vice_captain = db.session.query(Player).filter_by(id=team.vice_captain_id).first()
                
                if not captain or not vice_captain:
                    logger.error(f"Captain or vice-captain not found for team ID {team.id}")
                    return render_template('debug_error.html',
                                        match=match,
                                        error="Captain or vice-captain not found",
                                        params=test_params,
                                        team=team,
                                        team_players=team_players,
                                        traceback="Team generation completed but captain/vice-captain missing")
                
                logger.info(f"Captain: {captain.name}, Vice-captain: {vice_captain.name}")
                
                # Calculate team statistics for verification
                total_credits = sum(player.credit_points for _, player in team_players)
                if total_credits > 100:
                    logger.warning(f"Team exceeds credit limit: {total_credits}")
                
                # Count players by role
                role_counts = {}
                for _, player in team_players:
                    role = player.role
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                logger.info(f"Team role distribution: {role_counts}")
                
                # Count players by team
                team_counts = {}
                for _, player in team_players:
                    team_name = player.team_name
                    team_counts[team_name] = team_counts.get(team_name, 0) + 1
                
                logger.info(f"Team distribution: {team_counts}")
                
                return render_template('debug_team.html',
                                    match=match,
                                    team=team,
                                    team_players=team_players,
                                    captain=captain,
                                    vice_captain=vice_captain,
                                    params=test_params,
                                    role_counts=role_counts,
                                    team_counts=team_counts,
                                    total_credits=total_credits)
            else:
                logger.error("Debug team generation returned None but no error message")
                return render_template('debug_error.html',
                                    match=match,
                                    error="Team generation failed - returned None",
                                    params=test_params,
                                    team1_players=team1_players,
                                    team2_players=team2_players,
                                    team1_roles=team1_roles,
                                    team2_roles=team2_roles,
                                    traceback="Check logs for detailed error information")
        except Exception as e:
            logger.error(f"Error calling generate_auto_team: {str(e)}")
            logger.error(traceback.format_exc())
            debug_output.append(f"<div class='alert alert-danger'><strong>Error:</strong> {str(e)}</div>")
            return render_template('debug_error.html',
                                match=match,
                                error=str(e),
                                traceback=traceback.format_exc())
    except Exception as e:
        logger.error(f"Debug route error: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('debug_error.html',
                            match=match if 'match' in locals() else None,
                            error=f"Debug route error: {str(e)}",
                            traceback=traceback.format_exc())

# Helper functions for analytics
def team1_strength_description(team1_players):
    """Generate a description of team1's strengths"""
    avg_form = sum(p.current_form for p in team1_players) / len(team1_players) if team1_players else 0.5
    
    if avg_form > 0.7:
        return "excellent recent form"
    elif avg_form > 0.5:
        return "good form recently"
    else:
        return "been struggling in recent matches"

def team2_strength_description(team2_players):
    """Generate a description of team2's strengths"""
    avg_form = sum(p.current_form for p in team2_players) / len(team2_players) if team2_players else 0.5
    
    if avg_form > 0.7:
        return "been performing exceptionally well"
    elif avg_form > 0.5:
        return "shown consistent performance"
    else:
        return "room for improvement based on recent performances"

def calculate_avg_fantasy_points(players):
    """Calculate average fantasy points for a team's players"""
    if not players:
        return 30  # Default value
    
    # Use credit points as a proxy for fantasy points potential
    total_credits = sum(p.credit_points for p in players)
    return (total_credits / len(players)) * 5  # Scale to reasonable fantasy point range

def predict_match_score(team1_players, team2_players):
    """Predict a reasonable T20 match score"""
    team1_batting_strength = sum(p.current_form for p in team1_players if p.role in ['Batsman', 'All-Rounder']) / \
                            len([p for p in team1_players if p.role in ['Batsman', 'All-Rounder']]) if team1_players else 0.5
    
    team2_bowling_strength = sum(p.current_form for p in team2_players if p.role in ['Bowler', 'All-Rounder']) / \
                            len([p for p in team2_players if p.role in ['Bowler', 'All-Rounder']]) if team2_players else 0.5
    
    # Base score for T20
    base_score = 150
    
    # Adjust based on batting vs bowling strengths
    adjusted_score = base_score + (team1_batting_strength - team2_bowling_strength) * 50
    
    return int(max(120, min(220, adjusted_score)))

def generate_strategy_recommendation(team1_players, team2_players, match):
    """Generate a strategy recommendation based on team compositions"""
    # Count players by role
    team1_roles = {role: len([p for p in team1_players if p.role == role]) for role in ['Batsman', 'Bowler', 'All-Rounder', 'Wicket-Keeper']}
    team2_roles = {role: len([p for p in team2_players if p.role == role]) for role in ['Batsman', 'Bowler', 'All-Rounder', 'Wicket-Keeper']}
    
    # Calculate team strengths
    team1_batting = sum(p.current_form for p in team1_players if p.role in ['Batsman', 'All-Rounder', 'Wicket-Keeper']) / \
                   max(1, len([p for p in team1_players if p.role in ['Batsman', 'All-Rounder', 'Wicket-Keeper']]))
    
    team1_bowling = sum(p.current_form for p in team1_players if p.role in ['Bowler', 'All-Rounder']) / \
                   max(1, len([p for p in team1_players if p.role in ['Bowler', 'All-Rounder']]))
    
    team2_batting = sum(p.current_form for p in team2_players if p.role in ['Batsman', 'All-Rounder', 'Wicket-Keeper']) / \
                   max(1, len([p for p in team2_players if p.role in ['Batsman', 'All-Rounder', 'Wicket-Keeper']]))
    
    team2_bowling = sum(p.current_form for p in team2_players if p.role in ['Bowler', 'All-Rounder']) / \
                   max(1, len([p for p in team2_players if p.role in ['Bowler', 'All-Rounder']]))
    
    # Determine strategy based on team strengths
    if team1_batting > team2_batting and team1_bowling > team2_bowling:
        description = f"Our analysis suggests selecting more players from {match.team1} as they have stronger batting and bowling units based on current form."
        batsmen = 4
        bowlers = 3
        all_rounders = 3
        wicket_keepers = 1
        captain_strategy = f"Select a top batsman from {match.team1}"
        vice_captain_strategy = f"Select a bowling all-rounder from {match.team1}"
    elif team2_batting > team1_batting and team2_bowling > team1_bowling:
        description = f"Based on current form, {match.team2} appears stronger in both batting and bowling departments, suggesting more selections from their squad."
        batsmen = 4
        bowlers = 3
        all_rounders = 3
        wicket_keepers = 1
        captain_strategy = f"Select a top batsman from {match.team2}"
        vice_captain_strategy = f"Select a bowling all-rounder from {match.team2}"
    elif team1_batting > team2_batting and team2_bowling > team1_bowling:
        description = f"A balanced approach is recommended as {match.team1} has stronger batting while {match.team2} has stronger bowling."
        batsmen = 4
        bowlers = 4
        all_rounders = 2
        wicket_keepers = 1
        captain_strategy = f"Select a top batsman from {match.team1}"
        vice_captain_strategy = f"Select a top bowler from {match.team2}"
    elif team2_batting > team1_batting and team1_bowling > team2_bowling:
        description = f"Our analysis suggests a balanced team as {match.team2} has stronger batting while {match.team1} has stronger bowling."
        batsmen = 4
        bowlers = 4
        all_rounders = 2
        wicket_keepers = 1
        captain_strategy = f"Select a top batsman from {match.team2}"
        vice_captain_strategy = f"Select a top bowler from {match.team1}"
    else:
        description = "Both teams appear evenly matched. A balanced selection with players from both teams is recommended."
        batsmen = 3
        bowlers = 3
        all_rounders = 3
        wicket_keepers = 2
        captain_strategy = "Select the highest in-form batsman"
        vice_captain_strategy = "Select the highest in-form all-rounder"
    
    return {
        'description': description,
        'batsmen': batsmen,
        'bowlers': bowlers,
        'all_rounders': all_rounders,
        'wicket_keepers': wicket_keepers,
        'captain_strategy': captain_strategy,
        'vice_captain_strategy': vice_captain_strategy
    }

def generate_prediction_explanation(player):
    """Generate an explanation for player prediction"""
    points = player.get('predicted_points', 0)
    form = player.get('form', 0.5)
    role = player.get('role', 'Player')
    
    # Form description
    form_desc = "excellent" if form > 0.8 else "good" if form > 0.6 else "average" if form > 0.4 else "below average"
    
    # Point range description
    if points > 75:
        point_desc = "expected to be a top performer"
    elif points > 50:
        point_desc = "likely to score significant points"
    elif points > 30:
        point_desc = "should contribute decent points"
    else:
        point_desc = "may have limited impact"
    
    # Role-specific messages
    if role == 'Batsman':
        return f"In {form_desc} form and {point_desc}. Strong batting potential in this match."
    elif role == 'Bowler':
        return f"In {form_desc} form and {point_desc}. Conditions favor this bowler's style."
    elif role == 'All-Rounder':
        return f"In {form_desc} form and {point_desc}. Can contribute with both bat and ball."
    elif role == 'Wicket-Keeper':
        return f"In {form_desc} form and {point_desc}. Expected to contribute with batting and keeping."
    else:
        return f"In {form_desc} form. {point_desc} in this match."

def team2_strength_description(team2_players):
    """Generate a description of team2's strengths"""
    avg_form = sum(p.current_form for p in team2_players) / len(team2_players) if team2_players else 0.5
    
    if avg_form > 0.7:
        return "been performing exceptionally well"
    elif avg_form > 0.5:
        return "shown consistent performance"
    else:
        return "room for improvement based on recent performances"

def calculate_avg_fantasy_points(players):
    """Calculate average fantasy points for a team's players"""
    if not players:
        return 30  # Default value
    
    # Use credit points as a proxy for fantasy points potential
    total_credits = sum(p.credit_points for p in players)
    return (total_credits / len(players)) * 5  # Scale to reasonable fantasy point range

def predict_match_score(team1_players, team2_players):
    """Predict a reasonable T20 match score"""
    team1_batting_strength = sum(p.current_form for p in team1_players if p.role in ['Batsman', 'All-Rounder']) / \
                            len([p for p in team1_players if p.role in ['Batsman', 'All-Rounder']]) if team1_players else 0.5
    
    team2_bowling_strength = sum(p.current_form for p in team2_players if p.role in ['Bowler', 'All-Rounder']) / \
                            len([p for p in team2_players if p.role in ['Bowler', 'All-Rounder']]) if team2_players else 0.5
    
    # Base score for T20
    base_score = 150
    
    # Adjust based on batting vs bowling strengths
    adjusted_score = base_score + (team1_batting_strength - team2_bowling_strength) * 50
    
    return int(max(120, min(220, adjusted_score)))

def generate_strategy_recommendation(team1_players, team2_players, match):
    """Generate a strategy recommendation based on team compositions"""
    # Count players by role
    team1_roles = {role: len([p for p in team1_players if p.role == role]) for role in ['Batsman', 'Bowler', 'All-Rounder', 'Wicket-Keeper']}
    team2_roles = {role: len([p for p in team2_players if p.role == role]) for role in ['Batsman', 'Bowler', 'All-Rounder', 'Wicket-Keeper']}
    
    # Calculate team strengths
    team1_batting = sum(p.current_form for p in team1_players if p.role in ['Batsman', 'All-Rounder', 'Wicket-Keeper']) / \
                   max(1, len([p for p in team1_players if p.role in ['Batsman', 'All-Rounder', 'Wicket-Keeper']]))
    
    team1_bowling = sum(p.current_form for p in team1_players if p.role in ['Bowler', 'All-Rounder']) / \
                   max(1, len([p for p in team1_players if p.role in ['Bowler', 'All-Rounder']]))
    
    team2_batting = sum(p.current_form for p in team2_players if p.role in ['Batsman', 'All-Rounder', 'Wicket-Keeper']) / \
                   max(1, len([p for p in team2_players if p.role in ['Batsman', 'All-Rounder', 'Wicket-Keeper']]))
    
    team2_bowling = sum(p.current_form for p in team2_players if p.role in ['Bowler', 'All-Rounder']) / \
                   max(1, len([p for p in team2_players if p.role in ['Bowler', 'All-Rounder']]))
    
    # Determine strategy based on team strengths
    if team1_batting > team2_batting and team1_bowling > team2_bowling:
        description = f"Our analysis suggests selecting more players from {match.team1} as they have stronger batting and bowling units based on current form."
        batsmen = 4
        bowlers = 3
        all_rounders = 3
        wicket_keepers = 1
        captain_strategy = f"Select a top batsman from {match.team1}"
        vice_captain_strategy = f"Select a bowling all-rounder from {match.team1}"
    elif team2_batting > team1_batting and team2_bowling > team1_bowling:
        description = f"Based on current form, {match.team2} appears stronger in both batting and bowling departments, suggesting more selections from their squad."
        batsmen = 4
        bowlers = 3
        all_rounders = 3
        wicket_keepers = 1
        captain_strategy = f"Select a top batsman from {match.team2}"
        vice_captain_strategy = f"Select a bowling all-rounder from {match.team2}"
    elif team1_batting > team2_batting and team2_bowling > team1_bowling:
        description = f"A balanced approach is recommended as {match.team1} has stronger batting while {match.team2} has stronger bowling."
        batsmen = 4
        bowlers = 4
        all_rounders = 2
        wicket_keepers = 1
        captain_strategy = f"Select a top batsman from {match.team1}"
        vice_captain_strategy = f"Select a top bowler from {match.team2}"
    elif team2_batting > team1_batting and team1_bowling > team2_bowling:
        description = f"Our analysis suggests a balanced team as {match.team2} has stronger batting while {match.team1} has stronger bowling."
        batsmen = 4
        bowlers = 4
        all_rounders = 2
        wicket_keepers = 1
        captain_strategy = f"Select a top batsman from {match.team2}"
        vice_captain_strategy = f"Select a top bowler from {match.team1}"
    else:
        description = "Both teams appear evenly matched. A balanced selection with players from both teams is recommended."
        batsmen = 3
        bowlers = 3
        all_rounders = 3
        wicket_keepers = 2
        captain_strategy = "Select the highest in-form batsman"
        vice_captain_strategy = "Select the highest in-form all-rounder"
    
    return {
        'description': description,
        'batsmen': batsmen,
        'bowlers': bowlers,
        'all_rounders': all_rounders,
        'wicket_keepers': wicket_keepers,
        'captain_strategy': captain_strategy,
        'vice_captain_strategy': vice_captain_strategy
    }

def generate_prediction_explanation(player):
    """Generate an explanation for player prediction"""
    points = player.get('predicted_points', 0)
    form = player.get('form', 0.5)
    role = player.get('role', 'Player')
    
    # Form description
    form_desc = "excellent" if form > 0.8 else "good" if form > 0.6 else "average" if form > 0.4 else "below average"
    
    # Point range description
    if points > 75:
        point_desc = "expected to be a top performer"
    elif points > 50:
        point_desc = "likely to score significant points"
    elif points > 30:
        point_desc = "should contribute decent points"
    else:
        point_desc = "may have limited impact"
    
    # Role-specific messages
    if role == 'Batsman':
        return f"In {form_desc} form and {point_desc}. Strong batting potential in this match."
    elif role == 'Bowler':
        return f"In {form_desc} form and {point_desc}. Conditions favor this bowler's style."
    elif role == 'All-Rounder':
        return f"In {form_desc} form and {point_desc}. Can contribute with both bat and ball."
    elif role == 'Wicket-Keeper':
        return f"In {form_desc} form and {point_desc}. Expected to contribute with batting and keeping."
    else:
        return f"In {form_desc} form. {point_desc} in this match."

@frontend_bp.route('/populate-test-data')
@login_required
def populate_test_data():
    """Populate the database with test data for development and testing"""
    try:
        logger.info(f"Populating test data initiated by user: {current_user.id}")
        
        # Create test teams
        teams = ['Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers Bangalore', 'Delhi Capitals']
        
        # Create test venues first
        venue = Venue.query.filter_by(name='Test Stadium').first()
        if not venue:
            venue = Venue(
                name='Test Stadium',
                location='Test City',
                capacity=50000,
                pitch_type='Batting'
            )
            db.session.add(venue)
            db.session.commit()
            logger.info("Created test venue: Test Stadium")
        
        # Create sample venues if they don't exist
        venues = [
            Venue(name="Wankhede Stadium", location="Mumbai, India", capacity=33000),
            Venue(name="Lords", location="London, England", capacity=30000),
            Venue(name="MCG", location="Melbourne, Australia", capacity=100000),
            Venue(name="Eden Gardens", location="Kolkata, India", capacity=66000)
        ]
        
        for venue in venues:
            # Check if venue already exists
            existing_venue = Venue.query.filter_by(name=venue.name).first()
            if not existing_venue:
                db.session.add(venue)
        
        db.session.flush()
        
        # Get venue IDs
        venue_ids = [venue.id for venue in Venue.query.all()]
        
        # Create sample matches
        matches = [
            Match(team1="India", team2="Australia", date=datetime.now() + timedelta(days=1), venue_id=venue_ids[0], status="upcoming"),
            Match(team1="England", team2="South Africa", date=datetime.now() + timedelta(days=2), venue_id=venue_ids[1], status="upcoming"),
            Match(team1="New Zealand", team2="West Indies", date=datetime.now() + timedelta(days=3), venue_id=venue_ids[2], status="upcoming")
        ]
        
        for match in matches:
            # Check if match already exists
            existing_match = Match.query.filter_by(team1=match.team1, team2=match.team2).first()
            if not existing_match:
                db.session.add(match)
        
        db.session.flush()
        
        # Create test match
        match = Match.query.filter_by(team1='Mumbai Indians', team2='Chennai Super Kings').first()
        if not match:
            match = Match(
                team1='Mumbai Indians',
                team2='Chennai Super Kings',
                venue_id=venue.id,
                venue='Test Stadium',
                date=datetime.now() + timedelta(days=7),
                status='upcoming',
                format='T20'
            )
            db.session.add(match)
            db.session.commit()
            logger.info(f"Created test match: {match.team1} vs {match.team2}")
        else:
            logger.info(f"Using existing match: {match.team1} vs {match.team2}")
        
        # Check if players already exist
        existing_players = Player.query.count()
        if existing_players > 0:
            logger.info(f"Found {existing_players} existing players, skipping player creation")
        else:
            # Create test players for each team
            team_names = ["India", "Australia", "England", "South Africa", "New Zealand", "West Indies"]
            roles = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
            
            # Track player counts for reporting
            team_player_counts = {}
            role_counts = {}
            
            for team_name in team_names:
                team_player_counts[team_name] = 0
                
                # Create 4 batsmen
                for i in range(4):
                    # Check if player already exists
                    existing_player = Player.query.filter_by(name=f"{team_name} Batsman {i+1}").first()
                    if not existing_player:
                        player = Player(
                            name=f"{team_name} Batsman {i+1}",
                            team_name=team_name,
                            role="Batsman",
                            credit_points=random.uniform(7.0, 10.0),
                            current_form=random.uniform(0.0, 1.0)
                        )
                        db.session.add(player)
                        team_player_counts[team_name] += 1
                        role_counts["Batsman"] = role_counts.get("Batsman", 0) + 1
                
                # Create 4 bowlers
                for i in range(4):
                    existing_player = Player.query.filter_by(name=f"{team_name} Bowler {i+1}").first()
                    if not existing_player:
                        player = Player(
                            name=f"{team_name} Bowler {i+1}",
                            team_name=team_name,
                            role="Bowler",
                            credit_points=random.uniform(7.0, 10.0),
                            current_form=random.uniform(0.0, 1.0)
                        )
                        db.session.add(player)
                        team_player_counts[team_name] += 1
                        role_counts["Bowler"] = role_counts.get("Bowler", 0) + 1
                
                # Create 2 all-rounders
                for i in range(2):
                    existing_player = Player.query.filter_by(name=f"{team_name} All-Rounder {i+1}").first()
                    if not existing_player:
                        player = Player(
                            name=f"{team_name} All-Rounder {i+1}",
                            team_name=team_name,
                            role="All-Rounder",
                            credit_points=random.uniform(8.0, 10.0),
                            current_form=random.uniform(0.0, 1.0)
                        )
                        db.session.add(player)
                        team_player_counts[team_name] += 1
                        role_counts["All-Rounder"] = role_counts.get("All-Rounder", 0) + 1
                
                # Create 1 wicket-keeper
                existing_player = Player.query.filter_by(name=f"{team_name} Wicket-Keeper").first()
                if not existing_player:
                    player = Player(
                        name=f"{team_name} Wicket-Keeper",
                        team_name=team_name,
                        role="Wicket-Keeper",
                        credit_points=random.uniform(8.0, 10.0),
                        current_form=random.uniform(0.0, 1.0)
                    )
                    db.session.add(player)
                    team_player_counts[team_name] += 1
                    role_counts["Wicket-Keeper"] = role_counts.get("Wicket-Keeper", 0) + 1
            
            db.session.commit()
            
            # Get all matches for the template
            all_matches = Match.query.all()
            
            # Render the template with data summary
            return render_template('populate_test_data.html',
                                success=True,
                                matches=all_matches,
                                teams=team_player_counts,
                                roles=role_counts)
        
        flash('Test data has been populated successfully!', 'success')
        return redirect(url_for('frontend.matches'))
    
    except Exception as e:
        logger.error(f"Error populating test data: {str(e)}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return render_template('populate_test_data.html',
                            success=False,
                            error=str(e))

@frontend_bp.route('/populate-ipl-teams')
@login_required
def populate_ipl_teams():
    """Populate the database with IPL teams and players"""
    try:
        logger.info(f"Populating IPL teams initiated by user: {current_user.id}")
        
        # Create IPL teams match if it doesn't exist
        match = Match.query.filter_by(team1='Lucknow Super Giants', team2='Royal Challengers Bangalore').first()
        if not match:
            # Get a venue
            venue = Venue.query.first()
            if not venue:
                venue = Venue(
                    name='M. Chinnaswamy Stadium',
                    location='Bangalore, India',
                    capacity=40000,
                    pitch_type='Batting'
                )
                db.session.add(venue)
                db.session.commit()
                logger.info("Created venue: M. Chinnaswamy Stadium")
            
            match = Match(
                team1='Lucknow Super Giants',
                team2='Royal Challengers Bangalore',
                venue_id=venue.id,
                venue=venue.name,
                date=datetime.now() + timedelta(days=5),
                status='upcoming',
                format='T20'
            )
            db.session.add(match)
            db.session.commit()
            logger.info(f"Created IPL match: {match.team1} vs {match.team2}")
        else:
            logger.info(f"Using existing match: {match.team1} vs {match.team2}")
        
        # Add players for Lucknow Super Giants
        lsg_players = [
            # Batsmen
            {"name": "KL Rahul", "role": "Batsman", "credit_points": 9.5, "current_form": 0.85},
            {"name": "Quinton de Kock", "role": "Batsman", "credit_points": 9.0, "current_form": 0.8},
            {"name": "Deepak Hooda", "role": "Batsman", "credit_points": 8.5, "current_form": 0.75},
            {"name": "Manish Pandey", "role": "Batsman", "credit_points": 8.0, "current_form": 0.7},
            {"name": "Manan Vohra", "role": "Batsman", "credit_points": 7.5, "current_form": 0.65},
            
            # Bowlers
            {"name": "Avesh Khan", "role": "Bowler", "credit_points": 8.5, "current_form": 0.8},
            {"name": "Mohsin Khan", "role": "Bowler", "credit_points": 8.0, "current_form": 0.75},
            {"name": "Ravi Bishnoi", "role": "Bowler", "credit_points": 8.5, "current_form": 0.8},
            {"name": "Dushmantha Chameera", "role": "Bowler", "credit_points": 8.0, "current_form": 0.7},
            
            # All-Rounders
            {"name": "Marcus Stoinis", "role": "All-Rounder", "credit_points": 9.0, "current_form": 0.85},
            {"name": "Jason Holder", "role": "All-Rounder", "credit_points": 9.0, "current_form": 0.8},
            
            # Wicket-Keeper
            {"name": "Nicholas Pooran", "role": "Wicket-Keeper", "credit_points": 8.5, "current_form": 0.75}
        ]
        
        # Add players for Royal Challengers Bangalore
        rcb_players = [
            # Batsmen
            {"name": "Virat Kohli", "role": "Batsman", "credit_points": 10.0, "current_form": 0.9},
            {"name": "Faf du Plessis", "role": "Batsman", "credit_points": 9.5, "current_form": 0.85},
            {"name": "Glenn Maxwell", "role": "Batsman", "credit_points": 9.0, "current_form": 0.8},
            {"name": "Rajat Patidar", "role": "Batsman", "credit_points": 8.0, "current_form": 0.7},
            {"name": "Anuj Rawat", "role": "Batsman", "credit_points": 7.5, "current_form": 0.65},
            
            # Bowlers
            {"name": "Mohammed Siraj", "role": "Bowler", "credit_points": 8.5, "current_form": 0.8},
            {"name": "Josh Hazlewood", "role": "Bowler", "credit_points": 9.0, "current_form": 0.85},
            {"name": "Harshal Patel", "role": "Bowler", "credit_points": 8.5, "current_form": 0.8},
            {"name": "Wanindu Hasaranga", "role": "Bowler", "credit_points": 9.0, "current_form": 0.85},
            
            # All-Rounders
            {"name": "Shahbaz Ahmed", "role": "All-Rounder", "credit_points": 8.0, "current_form": 0.75},
            {"name": "David Willey", "role": "All-Rounder", "credit_points": 8.5, "current_form": 0.8},
            
            # Wicket-Keeper
            {"name": "Dinesh Karthik", "role": "Wicket-Keeper", "credit_points": 8.5, "current_form": 0.8}
        ]
        
        # Add Lucknow Super Giants players
        for player_data in lsg_players:
            existing_player = Player.query.filter_by(name=player_data["name"], team_name="Lucknow Super Giants").first()
            if not existing_player:
                player = Player(
                    name=player_data["name"],
                    team_name="Lucknow Super Giants",
                    role=player_data["role"],
                    credit_points=player_data["credit_points"],
                    current_form=player_data["current_form"]
                )
                db.session.add(player)
                logger.info(f"Added player: {player.name} ({player.role}) to Lucknow Super Giants")
        
        # Add Royal Challengers Bangalore players
        for player_data in rcb_players:
            existing_player = Player.query.filter_by(name=player_data["name"], team_name="Royal Challengers Bangalore").first()
            if not existing_player:
                player = Player(
                    name=player_data["name"],
                    team_name="Royal Challengers Bangalore",
                    role=player_data["role"],
                    credit_points=player_data["credit_points"],
                    current_form=player_data["current_form"]
                )
                db.session.add(player)
                logger.info(f"Added player: {player.name} ({player.role}) to Royal Challengers Bangalore")
        
        db.session.commit()
        
        # Count players for each team
        lsg_count = Player.query.filter_by(team_name="Lucknow Super Giants").count()
        rcb_count = Player.query.filter_by(team_name="Royal Challengers Bangalore").count()
        
        logger.info(f"Added {lsg_count} players to Lucknow Super Giants and {rcb_count} players to Royal Challengers Bangalore")
        
        flash(f'Successfully added {lsg_count} players to Lucknow Super Giants and {rcb_count} players to Royal Challengers Bangalore!', 'success')
        return redirect(url_for('frontend.matches'))
    except Exception as e:
        logger.error(f"Error populating IPL teams: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'Error populating IPL teams: {str(e)}', 'danger')
        return redirect(url_for('frontend.index'))