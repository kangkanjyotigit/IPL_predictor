from django.core.management.base import BaseCommand
from django.utils import timezone
from matches.models import Team, Match, Player, TeamPlayer
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Creates sample data for testing'

    def create_players(self):
        players_data = [
            {
                'name': 'Virat Kohli',
                'jersey_number': 18,
                'role': 'batsman',
                'batting_style': 'Right-handed',
                'bowling_style': 'Right-arm medium',
                'nationality': 'Indian',
                'date_of_birth': '1988-11-05'
            },
            {
                'name': 'Rohit Sharma',
                'jersey_number': 45,
                'role': 'batsman',
                'batting_style': 'Right-handed',
                'bowling_style': 'Right-arm off break',
                'nationality': 'Indian',
                'date_of_birth': '1987-04-30'
            },
            {
                'name': 'Jasprit Bumrah',
                'jersey_number': 93,
                'role': 'bowler',
                'batting_style': 'Right-handed',
                'bowling_style': 'Right-arm fast',
                'nationality': 'Indian',
                'date_of_birth': '1993-12-06'
            },
            {
                'name': 'Kane Williamson',
                'jersey_number': 22,
                'role': 'batsman',
                'batting_style': 'Right-handed',
                'bowling_style': 'Right-arm off break',
                'nationality': 'New Zealand',
                'date_of_birth': '1990-08-08'
            },
            {
                'name': 'Trent Boult',
                'jersey_number': 18,
                'role': 'bowler',
                'batting_style': 'Right-handed',
                'bowling_style': 'Left-arm fast',
                'nationality': 'New Zealand',
                'date_of_birth': '1989-07-22'
            }
        ]
        
        players = []
        for data in players_data:
            player, _ = Player.objects.get_or_create(
                name=data['name'],
                defaults={
                    'jersey_number': data['jersey_number'],
                    'role': data['role'],
                    'batting_style': data['batting_style'],
                    'bowling_style': data['bowling_style'],
                    'nationality': data['nationality'],
                    'date_of_birth': datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
                }
            )
            players.append(player)
        return players

    def handle(self, *args, **kwargs):
        # Create players
        players = self.create_players()
        
        # Create teams
        team1, _ = Team.objects.get_or_create(
            name='Mumbai Indians',
            defaults={
                'logo': 'https://example.com/mi-logo.png',
                'country': 'India'
            }
        )
        
        team2, _ = Team.objects.get_or_create(
            name='Chennai Super Kings',
            defaults={
                'logo': 'https://example.com/csk-logo.png',
                'country': 'India'
            }
        )

        # Add players to teams
        for player in players[:3]:
            TeamPlayer.objects.get_or_create(
                team=team1,
                player=player,
                defaults={
                    'is_captain': player.name == 'Rohit Sharma',
                    'is_keeper': False,
                    'joined_date': timezone.now().date()
                }
            )

        for player in players[3:]:
            TeamPlayer.objects.get_or_create(
                team=team2,
                player=player,
                defaults={
                    'is_captain': player.name == 'Kane Williamson',
                    'is_keeper': False,
                    'joined_date': timezone.now().date()
                }
            )

        # Create matches
        now = timezone.now()
        
        # Upcoming match
        Match.objects.get_or_create(
            title='MI vs CSK - Qualifier 1',
            defaults={
                'team1': team1,
                'team2': team2,
                'match_date': now + timedelta(days=1),
                'venue': 'Wankhede Stadium, Mumbai',
                'status': 'upcoming',
                'overs': 20,
                'match_type': 'T20',
                'description': 'IPL 2024 Qualifier 1'
            }
        )

        # Live match
        match, created = Match.objects.get_or_create(
            title='MI vs CSK - League Match',
            defaults={
                'team1': team1,
                'team2': team2,
                'match_date': now,
                'venue': 'MA Chidambaram Stadium, Chennai',
                'status': 'live',
                'team1_score': '120/4 (15.2)',
                'team2_score': '',
                'overs': 20,
                'match_type': 'T20',
                'description': 'IPL 2024 League Match',
                'current_innings': 1,
                'current_over': 15.2,
                'batting_team': team1,
                'bowling_team': team2
            }
        )

        # Completed match
        Match.objects.get_or_create(
            title='MI vs CSK - League Match',
            defaults={
                'team1': team1,
                'team2': team2,
                'match_date': now - timedelta(days=2),
                'venue': 'Eden Gardens, Kolkata',
                'status': 'completed',
                'team1_score': '185/6',
                'team2_score': '183/8',
                'winner': team1,
                'overs': 20,
                'match_type': 'T20',
                'description': 'IPL 2024 League Match'
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))
