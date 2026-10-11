import unittest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.team_generator import TeamGenerator
from src.utils.constants import PlayerRoles, TeamStrategies, CaptainPreferences


class TestTeamGenerator(unittest.TestCase):
    def setUp(self):
        # Create mock players for testing
        self.mock_players = []
        
        # Create batsmen
        for i in range(1, 6):
            player = MagicMock()
            player.id = i
            player.name = f"Batsman {i}"
            player.team_name = "Team A" if i <= 3 else "Team B"
            player.role = PlayerRoles.BATSMAN
            player.credit_points = 9.0
            player.current_form = 0.8 if i <= 2 else 0.6
            self.mock_players.append(player)
        
        # Create bowlers
        for i in range(6, 11):
            player = MagicMock()
            player.id = i
            player.name = f"Bowler {i-5}"
            player.team_name = "Team A" if i <= 8 else "Team B"
            player.role = PlayerRoles.BOWLER
            player.credit_points = 8.5
            player.current_form = 0.7 if i <= 7 else 0.5
            self.mock_players.append(player)
        
        # Create all-rounders
        for i in range(11, 16):
            player = MagicMock()
            player.id = i
            player.name = f"AllRounder {i-10}"
            player.team_name = "Team A" if i <= 13 else "Team B"
            player.role = PlayerRoles.ALL_ROUNDER
            player.credit_points = 9.5
            player.current_form = 0.9 if i <= 12 else 0.7
            self.mock_players.append(player)
        
        # Create wicket-keepers
        for i in range(16, 20):
            player = MagicMock()
            player.id = i
            player.name = f"WicketKeeper {i-15}"
            player.team_name = "Team A" if i <= 17 else "Team B"
            player.role = PlayerRoles.WICKET_KEEPER
            player.credit_points = 8.0
            player.current_form = 0.8 if i <= 16 else 0.6
            self.mock_players.append(player)
        
        # Set up the team generator
        self.team_generator = TeamGenerator(
            players=self.mock_players,
            max_players_per_team=7,
            max_credits=100,
            strategy=TeamStrategies.BALANCED,
            captain_preference=CaptainPreferences.FORM
        )

    def test_init(self):
        """Test the initialization of TeamGenerator"""
        self.assertEqual(len(self.team_generator.players), 19)
        self.assertEqual(self.team_generator.max_players_per_team, 7)
        self.assertEqual(self.team_generator.max_credits, 100)
        self.assertEqual(self.team_generator.strategy, TeamStrategies.BALANCED)
        self.assertEqual(self.team_generator.captain_preference, CaptainPreferences.FORM)

    def test_organize_players_by_role(self):
        """Test organizing players by role"""
        players_by_role = self.team_generator._organize_players_by_role()
        
        self.assertEqual(len(players_by_role[PlayerRoles.BATSMAN]), 5)
        self.assertEqual(len(players_by_role[PlayerRoles.BOWLER]), 5)
        self.assertEqual(len(players_by_role[PlayerRoles.ALL_ROUNDER]), 5)
        self.assertEqual(len(players_by_role[PlayerRoles.WICKET_KEEPER]), 4)

    def test_organize_players_by_team(self):
        """Test organizing players by team"""
        players_by_team = self.team_generator._organize_players_by_team()
        
        self.assertTrue("Team A" in players_by_team)
        self.assertTrue("Team B" in players_by_team)
        
        # Check that Team A has more players than Team B (as per our setup)
        self.assertTrue(len(players_by_team["Team A"]) > len(players_by_team["Team B"]))

    def test_calculate_player_score_form_strategy(self):
        """Test player score calculation with form strategy"""
        # Set strategy to form
        self.team_generator.strategy = TeamStrategies.FORM
        
        # Get a high form player and a low form player
        high_form_player = self.mock_players[0]  # Batsman 1 with form 0.8
        low_form_player = self.mock_players[4]   # Batsman 5 with form 0.6
        
        high_score = self.team_generator._calculate_player_score(high_form_player)
        low_score = self.team_generator._calculate_player_score(low_form_player)
        
        # High form player should have a higher score
        self.assertGreater(high_score, low_score)

    def test_calculate_player_score_value_strategy(self):
        """Test player score calculation with value strategy"""
        # Set strategy to value
        self.team_generator.strategy = TeamStrategies.VALUE
        
        # Create two players with same form but different credit points
        high_value_player = MagicMock()
        high_value_player.current_form = 0.7
        high_value_player.credit_points = 7.0  # Better value (more form per credit)
        
        low_value_player = MagicMock()
        low_value_player.current_form = 0.7
        low_value_player.credit_points = 10.0  # Worse value
        
        high_score = self.team_generator._calculate_player_score(high_value_player)
        low_score = self.team_generator._calculate_player_score(low_value_player)
        
        # High value player should have a higher score
        self.assertGreater(high_score, low_score)

    def test_select_players_balanced_strategy(self):
        """Test player selection with balanced strategy"""
        # Set strategy to balanced
        self.team_generator.strategy = TeamStrategies.BALANCED
        
        selected_players = self.team_generator.select_players()
        
        # Should have 11 players
        self.assertEqual(len(selected_players), 11)
        
        # Check role distribution
        roles_count = {role: 0 for role in PlayerRoles}
        for player in selected_players:
            roles_count[player.role] += 1
        
        # Should have at least 1 wicket keeper
        self.assertGreaterEqual(roles_count[PlayerRoles.WICKET_KEEPER], 1)
        # Should have at least 3 batsmen
        self.assertGreaterEqual(roles_count[PlayerRoles.BATSMAN], 3)
        # Should have at least 3 bowlers
        self.assertGreaterEqual(roles_count[PlayerRoles.BOWLER], 3)
        # Should have at least 1 all-rounder
        self.assertGreaterEqual(roles_count[PlayerRoles.ALL_ROUNDER], 1)

    def test_select_captain_and_vice_captain_form_preference(self):
        """Test captain and vice-captain selection with form preference"""
        # Set captain preference to form
        self.team_generator.captain_preference = CaptainPreferences.FORM
        
        # Create a set of players with different form values
        players = [
            MagicMock(id=1, current_form=0.9, name="Player 1"),
            MagicMock(id=2, current_form=0.8, name="Player 2"),
            MagicMock(id=3, current_form=0.7, name="Player 3"),
            MagicMock(id=4, current_form=0.6, name="Player 4"),
        ]
        
        captain, vice_captain = self.team_generator.select_captain_and_vice_captain(players)
        
        # Captain should be the player with highest form
        self.assertEqual(captain.id, 1)
        # Vice-captain should be the player with second highest form
        self.assertEqual(vice_captain.id, 2)

    def test_select_captain_and_vice_captain_credit_preference(self):
        """Test captain and vice-captain selection with credit preference"""
        # Set captain preference to credits
        self.team_generator.captain_preference = CaptainPreferences.CREDITS
        
        # Create a set of players with different credit values
        players = [
            MagicMock(id=1, credit_points=8.0, name="Player 1"),
            MagicMock(id=2, credit_points=9.0, name="Player 2"),
            MagicMock(id=3, credit_points=10.0, name="Player 3"),
            MagicMock(id=4, credit_points=7.0, name="Player 4"),
        ]
        
        captain, vice_captain = self.team_generator.select_captain_and_vice_captain(players)
        
        # Captain should be the player with highest credits
        self.assertEqual(captain.id, 3)
        # Vice-captain should be the player with second highest credits
        self.assertEqual(vice_captain.id, 2)

    def test_generate_team(self):
        """Test the complete team generation process"""
        team = self.team_generator.generate_team()
        
        # Check that we have a team with 11 players, a captain, and a vice-captain
        self.assertEqual(len(team['players']), 11)
        self.assertIsNotNone(team['captain'])
        self.assertIsNotNone(team['vice_captain'])
        
        # Check that captain and vice-captain are in the team
        captain_in_team = any(p.id == team['captain'].id for p in team['players'])
        vice_captain_in_team = any(p.id == team['vice_captain'].id for p in team['players'])
        self.assertTrue(captain_in_team)
        self.assertTrue(vice_captain_in_team)
        
        # Check that captain and vice-captain are different players
        self.assertNotEqual(team['captain'].id, team['vice_captain'].id)
        
        # Check that total credits don't exceed max credits
        total_credits = sum(p.credit_points for p in team['players'])
        self.assertLessEqual(total_credits, self.team_generator.max_credits)
        
        # Check team constraints
        team_counts = {}
        for player in team['players']:
            if player.team_name not in team_counts:
                team_counts[player.team_name] = 0
            team_counts[player.team_name] += 1
        
        for team_name, count in team_counts.items():
            self.assertLessEqual(count, self.team_generator.max_players_per_team)


if __name__ == '__main__':
    unittest.main()
