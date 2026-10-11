from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Match, Team, Player, Over, Ball, PlayerInnings
from .serializers import (
    MatchSerializer, TeamSerializer, PlayerSerializer,
    OverSerializer, BallSerializer, PlayerInningsSerializer
)

class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        team = self.get_object()
        matches = Match.objects.filter(Q(team1=team) | Q(team2=team))
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def players(self, request, pk=None):
        team = self.get_object()
        players = team.players.all()
        serializer = PlayerSerializer(players, many=True)
        return Response(serializer.data)

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def get_queryset(self):
        queryset = Match.objects.all()
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    @action(detail=True, methods=['post'])
    def toss(self, request, pk=None):
        match = self.get_object()
        winner_id = request.data.get('winner')
        decision = request.data.get('decision')
        
        if not winner_id or not decision:
            return Response(
                {'error': 'Both winner and decision are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        winner = get_object_or_404(Team, id=winner_id)
        if winner not in [match.team1, match.team2]:
            return Response(
                {'error': 'Invalid team'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        match.toss_winner = winner
        match.toss_decision = decision
        match.save()
        
        # Set batting and bowling teams based on toss
        if decision == 'bat':
            match.batting_team = winner
            match.bowling_team = match.team2 if winner == match.team1 else match.team1
        else:
            match.bowling_team = winner
            match.batting_team = match.team2 if winner == match.team1 else match.team1
        match.save()
        
        return Response(MatchSerializer(match).data)

    @action(detail=True, methods=['post'])
    def ball(self, request, pk=None):
        match = self.get_object()
        if match.status != 'live':
            return Response(
                {'error': 'Match is not live'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create the current over
        current_over = match.current_over
        over_number = int(current_over)
        ball_in_over = int((current_over * 10) % 10)

        over, created = Over.objects.get_or_create(
            match=match,
            over_number=over_number,
            innings=match.current_innings,
            defaults={
                'bowler': get_object_or_404(Player, id=request.data.get('bowler'))
            }
        )

        # Create the ball
        ball = Ball.objects.create(
            over=over,
            ball_number=ball_in_over + 1,
            batsman=get_object_or_404(Player, id=request.data.get('batsman')),
            runs_scored=request.data.get('runs', 0),
            is_wicket=request.data.get('is_wicket', False),
            wicket_type=request.data.get('wicket_type', ''),
            ball_type=request.data.get('ball_type', 'regular'),
            shot_type=request.data.get('shot_type'),
            commentary=request.data.get('commentary', '')
        )

        # Update match state
        if ball.ball_type == 'regular':
            match.current_over = float(f"{over_number}.{ball_in_over + 1}")
            if ball_in_over == 5:  # End of over
                match.current_over = float(over_number + 1)

        # Update player innings
        batting_innings, _ = PlayerInnings.objects.get_or_create(
            match=match,
            player=ball.batsman,
            team=match.batting_team,
            innings=match.current_innings
        )
        
        if ball.ball_type == 'regular':
            batting_innings.balls_faced += 1
        batting_innings.runs_scored += ball.runs_scored
        if ball.runs_scored == 4:
            batting_innings.fours += 1
        elif ball.runs_scored == 6:
            batting_innings.sixes += 1
        if ball.is_wicket:
            batting_innings.how_out = ball.wicket_type
        batting_innings.save()

        # Update over statistics
        over.runs += ball.runs_scored
        if ball.is_wicket:
            over.wickets += 1
        if ball.ball_type in ['wide', 'no_ball']:
            over.extras += 1
        over.save()

        match.save()
        return Response(BallSerializer(ball).data)

    @action(detail=True, methods=['post'])
    def start_match(self, request, pk=None):
        match = self.get_object()
        if match.status != 'upcoming':
            return Response(
                {'error': 'Match can only be started if it is upcoming'},
                status=status.HTTP_400_BAD_REQUEST
            )
        match.status = 'live'
        match.save()
        return Response(MatchSerializer(match).data)

    @action(detail=True, methods=['get'])
    def scorecard(self, request, pk=None):
        match = self.get_object()
        innings = request.query_params.get('innings', match.current_innings)
        
        player_innings = PlayerInnings.objects.filter(
            match=match,
            innings=innings
        ).select_related('player', 'team')
        
        batting = player_innings.exclude(balls_faced=0).order_by('-runs_scored')
        bowling = player_innings.exclude(overs_bowled=0).order_by('-wickets', 'runs_conceded')
        
        return Response({
            'batting': PlayerInningsSerializer(batting, many=True).data,
            'bowling': PlayerInningsSerializer(bowling, many=True).data
        })

    @action(detail=True, methods=['post'])
    def update_score(self, request, pk=None):
        match = self.get_object()
        team1_score = request.data.get('team1_score')
        team2_score = request.data.get('team2_score')
        winner_id = request.data.get('winner')

        if team1_score:
            match.team1_score = team1_score
        if team2_score:
            match.team2_score = team2_score
        if winner_id:
            winner = get_object_or_404(Team, id=winner_id)
            match.winner = winner
            match.status = 'completed'
        
        match.save()
        return Response(MatchSerializer(match).data)

@api_view(['GET'])
def upcoming_matches(request):
    matches = Match.objects.filter(
        status='upcoming',
        match_date__gte=timezone.now()
    ).order_by('match_date')[:5]
    serializer = MatchSerializer(matches, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def live_matches(request):
    matches = Match.objects.filter(status='live')
    serializer = MatchSerializer(matches, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def recent_matches(request):
    matches = Match.objects.filter(
        status='completed'
    ).order_by('-match_date')[:5]
    serializer = MatchSerializer(matches, many=True)
    return Response(serializer.data)
