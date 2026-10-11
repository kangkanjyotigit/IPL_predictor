from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from src.models import User, Player, Match, Team, Venue
from src.services.team_generator import TeamGenerator
from src.services.data_service import DataService
from src.database import db
import jwt
import datetime
import os

# Create Blueprint
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# Authentication middleware
def token_required(f):
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, os.environ.get('SECRET_KEY', 'dev-secret-key'), algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# API Resources
class UserRegistration(Resource):
    def post(self):
        data = request.get_json()
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
            return {'message': 'User already exists'}, 409
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        
        # Add user preferences if provided
        if 'preferred_sports' in data:
            new_user.preferred_sports = ','.join(data['preferred_sports'])
        if 'risk_profile' in data:
            new_user.risk_profile = data['risk_profile']
        if 'spending_limit' in data:
            new_user.spending_limit = data['spending_limit']
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        return {'message': 'User created successfully'}, 201


class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        
        # Find user by username
        user = User.query.filter_by(username=data['username']).first()
        
        # Check password
        if not user or not user.check_password(data['password']):
            return {'message': 'Invalid credentials'}, 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, os.environ.get('SECRET_KEY', 'dev-secret-key'), algorithm="HS256")
        
        # Update last login
        user.update_last_login()
        
        return {
            'token': token,
            'user': user.to_dict()
        }, 200


class UserProfile(Resource):
    @token_required
    def get(self, current_user):
        return current_user.to_dict(), 200
    
    @token_required
    def put(self, current_user):
        data = request.get_json()
        
        # Update user profile
        if 'username' in data:
            current_user.username = data['username']
        if 'email' in data:
            current_user.email = data['email']
        if 'password' in data:
            current_user.set_password(data['password'])
        if 'preferred_sports' in data:
            current_user.preferred_sports = ','.join(data['preferred_sports'])
        if 'risk_profile' in data:
            current_user.risk_profile = data['risk_profile']
        if 'spending_limit' in data:
            current_user.spending_limit = data['spending_limit']
        
        db.session.commit()
        
        return {'message': 'Profile updated successfully'}, 200


class MatchList(Resource):
    def get(self):
        # Get query parameters
        status = request.args.get('status', 'upcoming')
        limit = request.args.get('limit', 10, type=int)
        
        # Query matches
        if status == 'all':
            matches = Match.query.order_by(Match.start_time.desc()).limit(limit).all()
        else:
            matches = Match.query.filter_by(status=status).order_by(Match.start_time).limit(limit).all()
        
        # Return matches
        return jsonify([match.to_dict() for match in matches])


class MatchDetail(Resource):
    def get(self, match_id):
        match = Match.query.get_or_404(match_id)
        
        # Get venue and weather data if available
        venue_data = match.venue.to_dict() if match.venue else None
        weather_data = match.weather.to_dict() if match.weather else None
        
        # Combine match data with venue and weather
        match_data = match.to_dict()
        match_data['venue'] = venue_data
        match_data['weather'] = weather_data
        
        return match_data, 200


class PlayerList(Resource):
    def get(self):
        # Get query parameters
        team = request.args.get('team')
        player_type = request.args.get('player_type')
        search = request.args.get('search')
        limit = request.args.get('limit', 50, type=int)
        
        # Build query
        query = Player.query
        
        if team:
            query = query.filter_by(country=team)
        if player_type:
            query = query.filter_by(player_type=player_type)
        if search:
            query = query.filter(Player.name.ilike(f'%{search}%'))
        
        # Execute query
        players = query.limit(limit).all()
        
        # Return players
        return jsonify([player.to_dict() for player in players])


class PlayerDetail(Resource):
    def get(self, player_id):
        player = Player.query.get_or_404(player_id)
        
        # Get recent performances
        recent_performances = player.match_performances.order_by(
            db.desc('match_date')).limit(5).all()
        
        # Combine player data with performances
        player_data = player.to_dict()
        player_data['recent_performances'] = [perf.to_dict() for perf in recent_performances]
        
        return player_data, 200


class TeamPrediction(Resource):
    @token_required
    def post(self, current_user):
        data = request.get_json()
        match_id = data.get('match_id')
        risk_profile = data.get('risk_profile', current_user.risk_profile)
        
        # Validate match
        match = Match.query.get_or_404(match_id)
        
        # Initialize team generator
        team_generator = TeamGenerator(match_id, risk_profile)
        
        # Generate team recommendations
        recommendations = team_generator.generate_teams()
        
        return {
            'match': match.to_dict(),
            'recommendations': recommendations,
            'risk_profile': risk_profile
        }, 200


class PlayerPredictions(Resource):
    def get(self, match_id):
        # Validate match
        match = Match.query.get_or_404(match_id)
        
        # Since PredictionService is not available, return placeholder data
        # This is a temporary solution until a proper prediction service is implemented
        predictions = {
            'message': 'Player predictions feature is under development',
            'status': 'coming_soon'
        }
        
        return {
            'match': match.to_dict(),
            'predictions': predictions
        }, 200


class CaptainRecommendations(Resource):
    def get(self, match_id):
        # Validate match
        match = Match.query.get_or_404(match_id)
        
        # Since PredictionService is not available, return placeholder data
        # This is a temporary solution until a proper prediction service is implemented
        recommendations = {
            'message': 'Captain recommendations feature is under development',
            'status': 'coming_soon'
        }
        
        return {
            'match': match.to_dict(),
            'recommendations': recommendations
        }, 200


class DifferentialPicks(Resource):
    def get(self, match_id):
        # Validate match
        match = Match.query.get_or_404(match_id)
        
        # Since PredictionService is not available, return placeholder data
        # This is a temporary solution until a proper prediction service is implemented
        differentials = {
            'message': 'Differential picks feature is under development',
            'status': 'coming_soon'
        }
        
        return {
            'match': match.to_dict(),
            'differentials': differentials
        }, 200


class UserTeams(Resource):
    @token_required
    def get(self, current_user):
        # Get query parameters
        match_id = request.args.get('match_id')
        
        # Build query
        query = Team.query.filter_by(user_id=current_user.id)
        
        if match_id:
            query = query.filter_by(match_id=match_id)
        
        # Execute query
        teams = query.all()
        
        # Return teams
        return jsonify([team.to_dict() for team in teams])
    
    @token_required
    def post(self, current_user):
        data = request.get_json()
        
        # Create new team
        new_team = Team(
            user_id=current_user.id,
            match_id=data['match_id'],
            name=data['name'],
            risk_profile=data.get('risk_profile', current_user.risk_profile)
        )
        
        # Add players to team
        for player_data in data['players']:
            player = Player.query.get(player_data['id'])
            if player:
                new_team.add_player(
                    player,
                    is_captain=player_data.get('is_captain', False),
                    is_vice_captain=player_data.get('is_vice_captain', False)
                )
        
        # Save to database
        db.session.add(new_team)
        db.session.commit()
        
        return new_team.to_dict(), 201


class TeamDetail(Resource):
    @token_required
    def get(self, current_user, team_id):
        team = Team.query.get_or_404(team_id)
        
        # Check if team belongs to user
        if team.user_id != current_user.id:
            return {'message': 'Unauthorized'}, 401
        
        return team.to_dict(), 200
    
    @token_required
    def put(self, current_user, team_id):
        team = Team.query.get_or_404(team_id)
        
        # Check if team belongs to user
        if team.user_id != current_user.id:
            return {'message': 'Unauthorized'}, 401
        
        data = request.get_json()
        
        # Update team
        if 'name' in data:
            team.name = data['name']
        if 'risk_profile' in data:
            team.risk_profile = data['risk_profile']
        
        # Update players if provided
        if 'players' in data:
            # Remove all existing players
            for player in team.players:
                team.remove_player(player)
            
            # Add new players
            for player_data in data['players']:
                player = Player.query.get(player_data['id'])
                if player:
                    team.add_player(
                        player,
                        is_captain=player_data.get('is_captain', False),
                        is_vice_captain=player_data.get('is_vice_captain', False)
                    )
        
        db.session.commit()
        
        return team.to_dict(), 200
    
    @token_required
    def delete(self, current_user, team_id):
        team = Team.query.get_or_404(team_id)
        
        # Check if team belongs to user
        if team.user_id != current_user.id:
            return {'message': 'Unauthorized'}, 401
        
        db.session.delete(team)
        db.session.commit()
        
        return {'message': 'Team deleted successfully'}, 200


class VenueList(Resource):
    def get(self):
        venues = Venue.query.all()
        return jsonify([venue.to_dict() for venue in venues])


class VenueDetail(Resource):
    def get(self, venue_id):
        venue = Venue.query.get_or_404(venue_id)
        return venue.to_dict(), 200


class WeatherForecast(Resource):
    def get(self, match_id):
        match = Match.query.get_or_404(match_id)
        
        # Since Weather model is not available, return placeholder data
        # This is a temporary solution until weather forecasting is implemented
        weather_data = {
            'message': 'Weather forecast feature is under development',
            'status': 'coming_soon',
            'match_id': match_id,
            'venue': match.venue.name if match.venue else 'Unknown venue'
        }
        
        return {'match': match.to_dict(), 'weather': weather_data}, 200


# Register API resources
api.add_resource(UserRegistration, '/auth/register')
api.add_resource(UserLogin, '/auth/login')
api.add_resource(UserProfile, '/user/profile')
api.add_resource(MatchList, '/matches')
api.add_resource(MatchDetail, '/matches/<int:match_id>')
api.add_resource(PlayerList, '/players')
api.add_resource(PlayerDetail, '/players/<int:player_id>')
api.add_resource(TeamPrediction, '/predict/team')
api.add_resource(PlayerPredictions, '/predict/players/<int:match_id>')
api.add_resource(CaptainRecommendations, '/predict/captains/<int:match_id>')
api.add_resource(DifferentialPicks, '/predict/differentials/<int:match_id>')
api.add_resource(UserTeams, '/teams')
api.add_resource(TeamDetail, '/teams/<int:team_id>')
api.add_resource(VenueList, '/venues')
api.add_resource(VenueDetail, '/venues/<int:venue_id>')
api.add_resource(WeatherForecast, '/weather/<int:match_id>')
