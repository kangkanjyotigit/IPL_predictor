"""Advanced team optimization algorithms for Dream11 team generation"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import random
import itertools

from src.utils.constants import PlayerRoles, CaptainPreferences
from .prediction_service import PerformancePredictor

logger = logging.getLogger(__name__)

class TeamOptimizer:
    """Optimize team selection for Dream11"""
    
    # Dream11 constraints
    MAX_TEAM_SIZE = 11
    MAX_PLAYERS_PER_TEAM = 7  # Max players from a single team
    MIN_PLAYERS_PER_TEAM = 4  # Min players from a single team
    TOTAL_CREDITS = 100.0
    
    # Role constraints
    ROLE_CONSTRAINTS = {
        'Wicket-Keeper': {'min': 1, 'max': 4},
        'Batsman': {'min': 3, 'max': 6},
        'All-Rounder': {'min': 1, 'max': 4},
        'Bowler': {'min': 3, 'max': 6}
    }
    
    def __init__(self, performance_predictor=None):
        """Initialize the TeamOptimizer
        
        Args:
            performance_predictor: PerformancePredictor instance
        """
        self.performance_predictor = performance_predictor or PerformancePredictor()
    
    def optimize_team(self, match_id: str, team1_players: List[Dict], team2_players: List[Dict], 
                      captain_preference: str = CaptainPreferences.HIGHEST_POINTS,
                      vice_captain_preference: str = CaptainPreferences.SECOND_HIGHEST_POINTS,
                      budget_optimization: bool = True,
                      consider_opposition: bool = True,
                      min_batsmen: int = 3,
                      max_batsmen: int = 5,
                      min_bowlers: int = 3,
                      max_bowlers: int = 5,
                      min_all_rounders: int = 1,
                      max_all_rounders: int = 3,
                      min_wicket_keepers: int = 1,
                      max_wicket_keepers: int = 2) -> Tuple[List[Dict], Dict, Dict]:
        """Optimize team selection for Dream11
        
        Args:
            match_id: Match ID
            team1_players: List of players from team 1
            team2_players: List of players from team 2
            captain_preference: Captain selection preference
            vice_captain_preference: Vice captain selection preference
            budget_optimization: Whether to optimize for budget
            consider_opposition: Whether to consider opposition strengths
            min_batsmen: Minimum number of batsmen
            max_batsmen: Maximum number of batsmen
            min_bowlers: Minimum number of bowlers
            max_bowlers: Maximum number of bowlers
            min_all_rounders: Minimum number of all-rounders
            max_all_rounders: Maximum number of all-rounders
            min_wicket_keepers: Minimum number of wicket-keepers
            max_wicket_keepers: Maximum number of wicket-keepers
            
        Returns:
            Tuple of (selected players, captain, vice-captain)
        """
        try:
            # Update role constraints if customized
            role_constraints = self.ROLE_CONSTRAINTS.copy()
            role_constraints['Batsman'] = {'min': min_batsmen, 'max': max_batsmen}
            role_constraints['Bowler'] = {'min': min_bowlers, 'max': max_bowlers}
            role_constraints['All-Rounder'] = {'min': min_all_rounders, 'max': max_all_rounders}
            role_constraints['Wicket-Keeper'] = {'min': min_wicket_keepers, 'max': max_wicket_keepers}
            
            # Combine all players
            all_players = team1_players + team2_players
            
            # Predict points for all players
            for player in all_players:
                # Calculate predicted points if not already present
                if 'predicted_points' not in player:
                    # Predict points using our model
                    player['predicted_points'] = self.performance_predictor.predict_player_points(
                        player.get('id', ''), match_id, player
                    )
                    
                    # Generate a prediction message
                    player['prediction_explanation'] = self._generate_prediction_message(player)
            
            # Adjust points based on opposition strength if requested
            if consider_opposition:
                self._adjust_points_for_opposition(team1_players, team2_players)
            
            # Generate multiple team candidates
            candidates = self._generate_team_candidates(all_players, team1_players, team2_players, role_constraints, budget_optimization)
            
            # Select the best team
            best_team = self._select_best_team(candidates)
            
            # Select captain and vice-captain
            captain, vice_captain = self._select_captain_and_vice_captain(
                best_team, captain_preference, vice_captain_preference
            )
            
            return best_team, captain, vice_captain
        except Exception as e:
            logger.error(f"Error optimizing team: {str(e)}")
            raise
    
    def _generate_prediction_message(self, player: Dict) -> str:
        """Generate prediction explanation message for a player
        
        Args:
            player: Player data
            
        Returns:
            Prediction explanation
        """
        points = player.get('predicted_points', 0)
        form = player.get('current_form', 0.5)
        role = player.get('role', 'Player')
        
        # Form description
        form_desc = "excellent" if form > 0.8 else "good" if form > 0.6 else "average" if form > 0.4 else "poor"
        
        # Point range description
        if points > 75:
            point_desc = "an outstanding"
        elif points > 50:
            point_desc = "a very good"
        elif points > 30:
            point_desc = "a good"
        else:
            point_desc = "an average"
        
        # Role-specific messages
        if role == 'Batsman':
            return f"{player.get('name', 'Player')} is in {form_desc} form and is predicted to score {point_desc} {points:.1f} points. Expected to perform well with the bat."
        elif role == 'Bowler':
            return f"{player.get('name', 'Player')} is in {form_desc} form and is predicted to score {point_desc} {points:.1f} points. Could pick up valuable wickets."
        elif role == 'All-Rounder':
            return f"{player.get('name', 'Player')} is in {form_desc} form and is predicted to score {point_desc} {points:.1f} points. Can contribute with both bat and ball."
        elif role == 'Wicket-Keeper':
            return f"{player.get('name', 'Player')} is in {form_desc} form and is predicted to score {point_desc} {points:.1f} points. Expected to contribute with batting and keeping."
        else:
            return f"{player.get('name', 'Player')} is predicted to score {points:.1f} points."
    
    def _adjust_points_for_opposition(self, team1_players: List[Dict], team2_players: List[Dict]) -> None:
        """Adjust predicted points based on opposition strength
        
        Args:
            team1_players: Players from team 1
            team2_players: Players from team 2
        """
        # Calculate average bowling strength of team 2
        team2_bowling_strength = 0
        bowlers_count = 0
        for player in team2_players:
            if player.get('role') in ['Bowler', 'All-Rounder']:
                team2_bowling_strength += player.get('current_form', 0.5)
                bowlers_count += 1
        
        team2_bowling_strength = team2_bowling_strength / max(1, bowlers_count)
        
        # Calculate average bowling strength of team 1
        team1_bowling_strength = 0
        bowlers_count = 0
        for player in team1_players:
            if player.get('role') in ['Bowler', 'All-Rounder']:
                team1_bowling_strength += player.get('current_form', 0.5)
                bowlers_count += 1
        
        team1_bowling_strength = team1_bowling_strength / max(1, bowlers_count)
        
        # Adjust batting points based on opposition bowling strength
        for player in team1_players:
            if player.get('role') in ['Batsman', 'Wicket-Keeper', 'All-Rounder']:
                # Adjust down if facing strong bowling
                adjustment = (0.5 - team2_bowling_strength) * 10  # ±5 point adjustment
                player['predicted_points'] = max(0, player.get('predicted_points', 0) + adjustment)
        
        for player in team2_players:
            if player.get('role') in ['Batsman', 'Wicket-Keeper', 'All-Rounder']:
                # Adjust down if facing strong bowling
                adjustment = (0.5 - team1_bowling_strength) * 10  # ±5 point adjustment
                player['predicted_points'] = max(0, player.get('predicted_points', 0) + adjustment)
    
    def _generate_team_candidates(self, all_players: List[Dict], team1_players: List[Dict], 
                                 team2_players: List[Dict], role_constraints: Dict, 
                                 budget_optimization: bool) -> List[List[Dict]]:
        """Generate multiple team candidates that meet all constraints
        
        Args:
            all_players: All available players
            team1_players: Players from team 1
            team2_players: Players from team 2
            role_constraints: Role constraints
            budget_optimization: Whether to optimize for budget
            
        Returns:
            List of team candidates
        """
        # Sort players by predicted points
        sorted_players = sorted(all_players, key=lambda x: x.get('predicted_points', 0), reverse=True)
        
        # For better exploration, also create a list sorted by points per credit
        if budget_optimization:
            value_players = sorted(all_players, key=lambda x: x.get('predicted_points', 0) / max(0.1, x.get('credit_points', 10)), reverse=True)
        else:
            value_players = sorted_players.copy()
        
        # Generate multiple team candidates
        candidates = []
        
        # Approach 1: Greedy selection with role constraints
        greedy_team = self._greedy_selection(sorted_players, team1_players, team2_players, role_constraints)
        if greedy_team:
            candidates.append(greedy_team)
        
        # Approach 2: Value-based selection (points per credit)
        if budget_optimization:
            value_team = self._greedy_selection(value_players, team1_players, team2_players, role_constraints)
            if value_team and value_team not in candidates:
                candidates.append(value_team)
        
        # Approach 3: Balanced selection (ensure players from both teams)
        balanced_team = self._balanced_selection(sorted_players, team1_players, team2_players, role_constraints)
        if balanced_team and balanced_team not in candidates:
            candidates.append(balanced_team)
        
        # Approach 4: Role-weighted selection (prioritize specific roles)
        for priority_role in ['Batsman', 'Bowler', 'All-Rounder', 'Wicket-Keeper']:
            role_team = self._role_prioritized_selection(sorted_players, team1_players, team2_players, role_constraints, priority_role)
            if role_team and role_team not in candidates:
                candidates.append(role_team)
        
        # If we have no valid candidates, fall back to basic team
        if not candidates:
            logger.warning("Failed to generate team candidates using advanced methods, falling back to basic selection")
            basic_team = self._basic_selection(sorted_players, team1_players, team2_players)
            if basic_team:
                candidates.append(basic_team)
        
        return candidates
    
    def _greedy_selection(self, sorted_players: List[Dict], team1_players: List[Dict], 
                         team2_players: List[Dict], role_constraints: Dict) -> List[Dict]:
        """Greedy selection of players based on predicted points
        
        Args:
            sorted_players: Players sorted by predicted points
            team1_players: Players from team 1
            team2_players: Players from team 2
            role_constraints: Role constraints
            
        Returns:
            Selected team
        """
        team = []
        team1_count = 0
        team2_count = 0
        role_counts = {role: 0 for role in role_constraints}
        total_credits = 0
        
        for player in sorted_players:
            # Skip if player already in team
            if player in team:
                continue
            
            role = player.get('role')
            credits = player.get('credit_points', 10)
            team_name = player.get('team_name', '')
            
            # Check if adding this player would violate constraints
            # 1. Team size constraint
            if len(team) >= self.MAX_TEAM_SIZE:
                continue
            
            # 2. Credit constraint
            if total_credits + credits > self.TOTAL_CREDITS:
                continue
            
            # 3. Role constraint
            if role_counts.get(role, 0) >= role_constraints.get(role, {}).get('max', 0):
                continue
            
            # 4. Team constraint
            is_team1 = any(team_name.lower() == p.get('team_name', '').lower() for p in team1_players)
            if is_team1:
                if team1_count >= self.MAX_PLAYERS_PER_TEAM:
                    continue
            else:
                if team2_count >= self.MAX_PLAYERS_PER_TEAM:
                    continue
            
            # Add player to team
            team.append(player)
            role_counts[role] = role_counts.get(role, 0) + 1
            total_credits += credits
            if is_team1:
                team1_count += 1
            else:
                team2_count += 1
            
            # Check if we have a valid team
            if len(team) == self.MAX_TEAM_SIZE:
                # Validate role constraints
                valid = True
                for role, constraints in role_constraints.items():
                    if role_counts.get(role, 0) < constraints.get('min', 0):
                        valid = False
                        break
                
                # Validate team constraints
                if team1_count < self.MIN_PLAYERS_PER_TEAM or team2_count < self.MIN_PLAYERS_PER_TEAM:
                    valid = False
                
                if valid:
                    return team
        
        # If we can't form a valid team with greedy selection, return empty list
        return []
    
    def _balanced_selection(self, sorted_players: List[Dict], team1_players: List[Dict], 
                           team2_players: List[Dict], role_constraints: Dict) -> List[Dict]:
        """Balanced selection of players from both teams
        
        Args:
            sorted_players: Players sorted by predicted points
            team1_players: Players from team 1
            team2_players: Players from team 2
            role_constraints: Role constraints
            
        Returns:
            Selected team
        """
        # Start with a balanced set of players from each team
        team1_sorted = sorted(team1_players, key=lambda x: x.get('predicted_points', 0), reverse=True)
        team2_sorted = sorted(team2_players, key=lambda x: x.get('predicted_points', 0), reverse=True)
        
        team = []
        role_counts = {role: 0 for role in role_constraints}
        total_credits = 0
        
        # Alternately pick players from each team
        for i in range(self.MAX_TEAM_SIZE):
            if i % 2 == 0 and team1_sorted:
                source_list = team1_sorted
            elif team2_sorted:
                source_list = team2_sorted
            else:
                break
            
            # Find the best player that fits constraints
            for idx, player in enumerate(source_list):
                role = player.get('role')
                credits = player.get('credit_points', 10)
                
                # Check if adding this player would violate constraints
                # 1. Credit constraint
                if total_credits + credits > self.TOTAL_CREDITS:
                    continue
                
                # 2. Role constraint
                if role_counts.get(role, 0) >= role_constraints.get(role, {}).get('max', 0):
                    continue
                
                # Add player to team
                team.append(player)
                role_counts[role] = role_counts.get(role, 0) + 1
                total_credits += credits
                source_list.pop(idx)
                break
        
        # Fill remaining slots with best available players
        remaining_slots = self.MAX_TEAM_SIZE - len(team)
        for player in sorted_players:
            if remaining_slots <= 0:
                break
                
            # Skip if player already in team
            if player in team:
                continue
            
            role = player.get('role')
            credits = player.get('credit_points', 10)
            team_name = player.get('team_name', '')
            
            # Check if adding this player would violate constraints
            # 1. Credit constraint
            if total_credits + credits > self.TOTAL_CREDITS:
                continue
            
            # 2. Role constraint
            if role_counts.get(role, 0) >= role_constraints.get(role, {}).get('max', 0):
                continue
            
            # 3. Team constraint
            is_team1 = any(team_name.lower() == p.get('team_name', '').lower() for p in team1_players)
            team1_count = sum(1 for p in team if any(p.get('team_name', '').lower() == t.get('team_name', '').lower() for t in team1_players))
            team2_count = len(team) - team1_count
            
            if is_team1:
                if team1_count >= self.MAX_PLAYERS_PER_TEAM:
                    continue
            else:
                if team2_count >= self.MAX_PLAYERS_PER_TEAM:
                    continue
            
            # Add player to team
            team.append(player)
            role_counts[role] = role_counts.get(role, 0) + 1
            total_credits += credits
            remaining_slots -= 1
        
        # Check if we have a valid team
        if len(team) == self.MAX_TEAM_SIZE:
            # Validate role constraints
            valid = True
            for role, constraints in role_constraints.items():
                if role_counts.get(role, 0) < constraints.get('min', 0):
                    valid = False
                    break
            
            # Validate team constraints
            team1_count = sum(1 for p in team if any(p.get('team_name', '').lower() == t.get('team_name', '').lower() for t in team1_players))
            team2_count = len(team) - team1_count
            if team1_count < self.MIN_PLAYERS_PER_TEAM or team2_count < self.MIN_PLAYERS_PER_TEAM:
                valid = False
            
            if valid:
                return team
        
        # If we can't form a valid team, return empty list
        return []
    
    def _role_prioritized_selection(self, sorted_players: List[Dict], team1_players: List[Dict], 
                                  team2_players: List[Dict], role_constraints: Dict, 
                                  priority_role: str) -> List[Dict]:
        """Selection prioritizing a specific role
        
        Args:
            sorted_players: Players sorted by predicted points
            team1_players: Players from team 1
            team2_players: Players from team 2
            role_constraints: Role constraints
            priority_role: Role to prioritize
            
        Returns:
            Selected team
        """
        # Start with the best players of the priority role
        priority_players = [p for p in sorted_players if p.get('role') == priority_role]
        other_players = [p for p in sorted_players if p.get('role') != priority_role]
        
        # Take maximum allowed priority role players
        max_priority = role_constraints.get(priority_role, {}).get('max', 4)
        priority_selection = priority_players[:max_priority]
        
        # Calculate initial state
        team = priority_selection.copy()
        role_counts = {role: 0 for role in role_constraints}
        role_counts[priority_role] = len(priority_selection)
        total_credits = sum(p.get('credit_points', 10) for p in priority_selection)
        team1_count = sum(1 for p in team if any(p.get('team_name', '').lower() == t.get('team_name', '').lower() for t in team1_players))
        team2_count = len(team) - team1_count
        
        # Fill remaining slots with best available players
        remaining_slots = self.MAX_TEAM_SIZE - len(team)
        for player in other_players:
            if remaining_slots <= 0:
                break
                
            # Skip if player already in team
            if player in team:
                continue
            
            role = player.get('role')
            credits = player.get('credit_points', 10)
            team_name = player.get('team_name', '')
            
            # Check if adding this player would violate constraints
            # 1. Credit constraint
            if total_credits + credits > self.TOTAL_CREDITS:
                continue
            
            # 2. Role constraint
            if role_counts.get(role, 0) >= role_constraints.get(role, {}).get('max', 0):
                continue
            
            # 3. Team constraint
            is_team1 = any(team_name.lower() == p.get('team_name', '').lower() for p in team1_players)
            if is_team1:
                if team1_count >= self.MAX_PLAYERS_PER_TEAM:
                    continue
            else:
                if team2_count >= self.MAX_PLAYERS_PER_TEAM:
                    continue
            
            # Add player to team
            team.append(player)
            role_counts[role] = role_counts.get(role, 0) + 1
            total_credits += credits
            if is_team1:
                team1_count += 1
            else:
                team2_count += 1
            remaining_slots -= 1
        
        # Check if we have a valid team
        if len(team) == self.MAX_TEAM_SIZE:
            # Validate role constraints
            valid = True
            for role, constraints in role_constraints.items():
                if role_counts.get(role, 0) < constraints.get('min', 0):
                    valid = False
                    break
            
            # Validate team constraints
            if team1_count < self.MIN_PLAYERS_PER_TEAM or team2_count < self.MIN_PLAYERS_PER_TEAM:
                valid = False
            
            if valid:
                return team
        
        # If we can't form a valid team, return empty list
        return []
    
    def _basic_selection(self, sorted_players: List[Dict], team1_players: List[Dict], 
                       team2_players: List[Dict]) -> List[Dict]:
        """Basic selection of players without strict constraint checks
        
        Args:
            sorted_players: Players sorted by predicted points
            team1_players: Players from team 1
            team2_players: Players from team 2
            
        Returns:
            Selected team
        """
        # Select players by role
        wicket_keepers = [p for p in sorted_players if p.get('role') == 'Wicket-Keeper'][:2]
        batsmen = [p for p in sorted_players if p.get('role') == 'Batsman'][:4]
        all_rounders = [p for p in sorted_players if p.get('role') == 'All-Rounder'][:2]
        bowlers = [p for p in sorted_players if p.get('role') == 'Bowler'][:4]
        
        # Combine and remove duplicates (a player might be in multiple lists)
        combined = []
        for player in wicket_keepers + batsmen + all_rounders + bowlers:
            if player not in combined:
                combined.append(player)
        
        # Take top 11 or fewer if not enough players
        return combined[:min(11, len(combined))]
    
    def _select_best_team(self, candidates: List[List[Dict]]) -> List[Dict]:
        """Select the best team from candidates
        
        Args:
            candidates: List of team candidates
            
        Returns:
            Best team
        """
        if not candidates:
            return []
        
        # Calculate total predicted points for each team
        team_points = []
        for team in candidates:
            total_points = sum(player.get('predicted_points', 0) for player in team)
            team_points.append((team, total_points))
        
        # Sort by total points
        team_points.sort(key=lambda x: x[1], reverse=True)
        
        # Return the team with highest points
        return team_points[0][0]
    
    def _select_captain_and_vice_captain(self, team: List[Dict], 
                                        captain_preference: str, 
                                        vice_captain_preference: str) -> Tuple[Dict, Dict]:
        """Select captain and vice-captain based on preferences
        
        Args:
            team: Selected team
            captain_preference: Captain preference
            vice_captain_preference: Vice-captain preference
            
        Returns:
            Tuple of (captain, vice-captain)
        """
        if not team:
            return {}, {}
        
        # Sort team by predicted points
        sorted_team = sorted(team, key=lambda x: x.get('predicted_points', 0), reverse=True)
        
        # Default: highest points
        captain = sorted_team[0]
        vice_captain = sorted_team[1]
        
        # Apply captain preference
        if captain_preference == CaptainPreferences.HIGHEST_POINTS:
            # Already set as default
            pass
        elif captain_preference == CaptainPreferences.BEST_FORM or captain_preference == CaptainPreferences.FORM:
            # Sort by current form
            form_sorted = sorted(team, key=lambda x: x.get('current_form', 0), reverse=True)
            captain = form_sorted[0]
        elif captain_preference == CaptainPreferences.SECOND_HIGHEST_POINTS:
            # Use second highest points
            captain = sorted_team[1] if len(sorted_team) > 1 else sorted_team[0]
        elif captain_preference == CaptainPreferences.DIFFERENT_TEAM:
            # Captain from different team than highest points player
            captain_team = sorted_team[0].get('team_name', '')
            for player in sorted_team[1:]:
                if player.get('team_name', '') != captain_team:
                    captain = player
                    break
        elif captain_preference == CaptainPreferences.DIFFERENT_ROLE:
            # Captain with different role than highest points player
            captain_role = sorted_team[0].get('role', '')
            for player in sorted_team[1:]:
                if player.get('role', '') != captain_role:
                    captain = player
                    break
        
        # Apply vice-captain preference
        if vice_captain_preference == CaptainPreferences.HIGHEST_POINTS:
            # Use highest points player who is not captain
            for player in sorted_team:
                if player != captain:
                    vice_captain = player
                    break
        elif vice_captain_preference == CaptainPreferences.BEST_FORM or vice_captain_preference == CaptainPreferences.FORM:
            # Sort by current form and select first who is not captain
            form_sorted = sorted(team, key=lambda x: x.get('current_form', 0), reverse=True)
            for player in form_sorted:
                if player != captain:
                    vice_captain = player
                    break
        elif vice_captain_preference == CaptainPreferences.SECOND_HIGHEST_POINTS:
            # Use second highest points player who is not captain
            for player in sorted_team:
                if player != captain:
                    vice_captain = player
                    break
        elif vice_captain_preference == CaptainPreferences.DIFFERENT_TEAM:
            # Vice-captain from different team than captain
            captain_team = captain.get('team_name', '')
            for player in sorted_team:
                if player != captain and player.get('team_name', '') != captain_team:
                    vice_captain = player
                    break
            else:
                # If no player from different team, use highest points player who is not captain
                for player in sorted_team:
                    if player != captain:
                        vice_captain = player
                        break
        elif vice_captain_preference == CaptainPreferences.DIFFERENT_ROLE:
            # Vice-captain with different role than captain
            captain_role = captain.get('role', '')
            for player in sorted_team:
                if player != captain and player.get('role', '') != captain_role:
                    vice_captain = player
                    break
            else:
                # If no player with different role, use highest points player who is not captain
                for player in sorted_team:
                    if player != captain:
                        vice_captain = player
                        break
        
        # Ensure vice_captain is not the same as captain
        if vice_captain == captain and len(team) > 1:
            for player in sorted_team:
                if player != captain:
                    vice_captain = player
                    break
        
        return captain, vice_captain
