from rest_framework import serializers
from .models import Match, Team, Player, Over, Ball, PlayerInnings, TeamPlayer

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'name', 'jersey_number', 'role', 'batting_style', 'bowling_style', 'nationality']

class TeamPlayerSerializer(serializers.ModelSerializer):
    player = PlayerSerializer()
    
    class Meta:
        model = TeamPlayer
        fields = ['player', 'is_captain', 'is_keeper', 'joined_date']

class TeamSerializer(serializers.ModelSerializer):
    players = TeamPlayerSerializer(source='teamplayer_set', many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'logo', 'country', 'players', 'created_at']

class BallSerializer(serializers.ModelSerializer):
    batsman_details = PlayerSerializer(source='batsman', read_only=True)
    
    class Meta:
        model = Ball
        fields = [
            'id', 'ball_number', 'batsman', 'batsman_details',
            'runs_scored', 'is_wicket', 'wicket_type',
            'ball_type', 'shot_type', 'commentary'
        ]

class OverSerializer(serializers.ModelSerializer):
    balls = BallSerializer(many=True, read_only=True)
    bowler_details = PlayerSerializer(source='bowler', read_only=True)
    
    class Meta:
        model = Over
        fields = [
            'id', 'over_number', 'bowler', 'bowler_details',
            'runs', 'wickets', 'extras', 'innings', 'balls'
        ]

class PlayerInningsSerializer(serializers.ModelSerializer):
    player_details = PlayerSerializer(source='player', read_only=True)
    
    class Meta:
        model = PlayerInnings
        fields = [
            'id', 'player', 'player_details', 'team', 'innings',
            'runs_scored', 'balls_faced', 'fours', 'sixes', 'how_out',
            'overs_bowled', 'runs_conceded', 'wickets', 'maidens'
        ]

class MatchSerializer(serializers.ModelSerializer):
    team1_details = TeamSerializer(source='team1', read_only=True)
    team2_details = TeamSerializer(source='team2', read_only=True)
    winner_details = TeamSerializer(source='winner', read_only=True)
    toss_winner_details = TeamSerializer(source='toss_winner', read_only=True)
    batting_team_details = TeamSerializer(source='batting_team', read_only=True)
    bowling_team_details = TeamSerializer(source='bowling_team', read_only=True)
    overs = OverSerializer(source='over_records', many=True, read_only=True)
    player_innings = PlayerInningsSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'title', 
            'team1', 'team2', 'team1_details', 'team2_details',
            'match_date', 'venue', 'status',
            'toss_winner', 'toss_winner_details', 'toss_decision',
            'team1_score', 'team2_score',
            'winner', 'winner_details',
            'overs', 'match_type', 'description',
            'current_innings', 'current_over',
            'batting_team', 'batting_team_details',
            'bowling_team', 'bowling_team_details',
            'player_innings',
            'created_at', 'updated_at'
        ]
