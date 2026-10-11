"""
Team Generator Service for Dream11 Prediction
This module provides functionality for auto-generating teams based on various strategies and constraints.
"""

from src.models.player import Player
from src.models.team import Team, TeamPlayer
from src.models.match import Match
from src.utils.constants import TeamStrategies, CaptainPreferences, PlayerRoles
import random
import logging
import traceback
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logger = logging.getLogger(__name__)

class TeamGenerationError(Exception):
    """Custom exception for team generation errors"""
    pass

class TeamGenerator:
    """Class to handle team generation logic"""
    
    def __init__(self, match_id, user_id, db, **kwargs):
        """Initialize the team generator with parameters"""
        try:
            logger.info(f"Initializing TeamGenerator for match_id={match_id}, user_id={user_id}")
            logger.debug(f"Team generation parameters: {kwargs}")
            
            # Ensure parameters are of the correct type
            try:
                self.match_id = int(match_id)
                self.user_id = int(user_id)
            except (ValueError, TypeError) as e:
                logger.error(f"Type conversion error in TeamGenerator.__init__: {str(e)}")
                raise TeamGenerationError(f"Invalid parameter types: {str(e)}")
                
            self.db = db
            
            # Set default parameters with type conversion
            self.team_name = str(kwargs.get('team_name', 'Auto Team'))
            self.strategy = str(kwargs.get('strategy', TeamStrategies.BALANCED))
            
            # Convert numeric parameters with defaults and validation
            try:
                self.max_players_from_team = int(kwargs.get('max_players_from_team', 7))
                if self.max_players_from_team < 1 or self.max_players_from_team > 11:
                    logger.warning(f"Invalid max_players_from_team value: {self.max_players_from_team}, setting to default 7")
                    self.max_players_from_team = 7
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting max_players_from_team: {str(e)}, using default value 7")
                self.max_players_from_team = 7
            
            try:
                self.form_weight = float(kwargs.get('form_weight', 0.5))
                if self.form_weight < 0 or self.form_weight > 1:
                    logger.warning(f"Invalid form_weight value: {self.form_weight}, setting to default 0.5")
                    self.form_weight = 0.5
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting form_weight: {str(e)}, using default value 0.5")
                self.form_weight = 0.5
            
            try:
                self.credit_weight = float(kwargs.get('credit_weight', 0.5))
                if self.credit_weight < 0 or self.credit_weight > 1:
                    logger.warning(f"Invalid credit_weight value: {self.credit_weight}, setting to default 0.5")
                    self.credit_weight = 0.5
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting credit_weight: {str(e)}, using default value 0.5")
                self.credit_weight = 0.5
            
            # Validate captain preference with fallback to default
            captain_pref = str(kwargs.get('captain_preference', CaptainPreferences.HIGHEST_POINTS))
            valid_captain_prefs = [CaptainPreferences.HIGHEST_POINTS, CaptainPreferences.BEST_FORM, 
                               CaptainPreferences.FORM, CaptainPreferences.ALL_ROUNDER, 
                               CaptainPreferences.BATSMAN, CaptainPreferences.BOWLER]
            
            if captain_pref not in valid_captain_prefs:
                logger.warning(f"Invalid captain preference: {captain_pref}, using default (HIGHEST_POINTS)")
                self.captain_preference = CaptainPreferences.HIGHEST_POINTS
            else:
                self.captain_preference = captain_pref
                
            # For backward compatibility, map FORM to BEST_FORM
            if self.captain_preference == CaptainPreferences.FORM:
                self.captain_preference = CaptainPreferences.BEST_FORM
                logger.info("Mapped captain preference FORM to BEST_FORM for compatibility")
            
            # Validate vice captain preference with fallback to default
            vice_captain_pref = str(kwargs.get('vice_captain_preference', CaptainPreferences.SECOND_HIGHEST_POINTS))
            valid_vice_captain_prefs = [CaptainPreferences.SECOND_HIGHEST_POINTS, 
                                    CaptainPreferences.DIFFERENT_TEAM, 
                                    CaptainPreferences.DIFFERENT_ROLE]
            
            if vice_captain_pref not in valid_vice_captain_prefs:
                logger.warning(f"Invalid vice captain preference: {vice_captain_pref}, using default (SECOND_HIGHEST_POINTS)")
                self.vice_captain_preference = CaptainPreferences.SECOND_HIGHEST_POINTS
            else:
                self.vice_captain_preference = vice_captain_pref
            
            # Convert boolean parameters with defaults
            try:
                self.consider_opposition = bool(kwargs.get('consider_opposition', False))
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting consider_opposition: {str(e)}, using default value False")
                self.consider_opposition = False
                
            try:
                self.apply_budget_optimization = bool(kwargs.get('apply_budget_optimization', True))
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting apply_budget_optimization: {str(e)}, using default value True")
                self.apply_budget_optimization = True
            
            # Validate weights sum to 1.0 (approximately)
            if abs(self.form_weight + self.credit_weight - 1.0) > 0.01:
                logger.warning(f"Form weight ({self.form_weight}) and credit weight ({self.credit_weight}) do not sum to 1.0, adjusting")
                total = self.form_weight + self.credit_weight
                if total > 0:
                    self.form_weight = self.form_weight / total
                    self.credit_weight = self.credit_weight / total
                else:
                    self.form_weight = 0.5
                    self.credit_weight = 0.5
            
            # Get match details
            self.match = self.db.session.query(Match).filter_by(id=match_id).first()
            if not self.match:
                raise TeamGenerationError(f"Match with ID {match_id} not found")
            
            # Get players for both teams
            self.team1_players = self.db.session.query(Player).filter_by(team_name=self.match.team1).all()
            if not self.team1_players:
                raise TeamGenerationError(f"No players found for team {self.match.team1}")
                
            self.team2_players = self.db.session.query(Player).filter_by(team_name=self.match.team2).all()
            if not self.team2_players:
                raise TeamGenerationError(f"No players found for team {self.match.team2}")
            
            logger.info(f"Found {len(self.team1_players)} players for {self.match.team1} and {len(self.team2_players)} players for {self.match.team2}")
            
            # Organize players by role
            self.players_by_role = defaultdict(list)
            self.players_by_team = {
                self.match.team1: defaultdict(list),
                self.match.team2: defaultdict(list)
            }
            
            for player in self.team1_players + self.team2_players:
                normalized_role = PlayerRoles.normalize_role(player.role)
                self.players_by_role[normalized_role].append(player)
                self.players_by_team[player.team_name][normalized_role].append(player)
        
        except TeamGenerationError as e:
            logger.error(f"Team generation initialization failed: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error during team generation initialization: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def get_role_requirements(self):
        """Get the required number of players for each role based on strategy"""
        if self.strategy == TeamStrategies.BALANCED:
            return {
                PlayerRoles.WICKET_KEEPER: (1, 1),  # (min, max)
                PlayerRoles.BATSMAN: (3, 5),
                PlayerRoles.BOWLER: (3, 5),
                PlayerRoles.ALL_ROUNDER: (2, 4)
            }
        elif self.strategy == TeamStrategies.AGGRESSIVE:
            return {
                PlayerRoles.WICKET_KEEPER: (1, 1),
                PlayerRoles.BATSMAN: (4, 6),
                PlayerRoles.BOWLER: (2, 4),
                PlayerRoles.ALL_ROUNDER: (2, 4)
            }
        elif self.strategy == TeamStrategies.DEFENSIVE:
            return {
                PlayerRoles.WICKET_KEEPER: (1, 1),
                PlayerRoles.BATSMAN: (2, 4),
                PlayerRoles.BOWLER: (4, 6),
                PlayerRoles.ALL_ROUNDER: (2, 4)
            }
        elif self.strategy == TeamStrategies.ALL_ROUNDERS:
            return {
                PlayerRoles.WICKET_KEEPER: (1, 1),
                PlayerRoles.BATSMAN: (2, 4),
                PlayerRoles.BOWLER: (2, 4),
                PlayerRoles.ALL_ROUNDER: (4, 6)
            }
        else:
            # Default to balanced
            return {
                PlayerRoles.WICKET_KEEPER: (1, 1),
                PlayerRoles.BATSMAN: (3, 5),
                PlayerRoles.BOWLER: (3, 5),
                PlayerRoles.ALL_ROUNDER: (2, 4)
            }
    
    def calculate_player_score(self, player):
        """Calculate a score for a player based on form and credits"""
        # Base score is a weighted combination of form and credits
        form_score = player.current_form * self.form_weight
        credit_score = (player.credit_points / 10) * self.credit_weight  # Normalize credits to 0-1 range
        
        # Apply strategy-specific adjustments
        role_multiplier = 1.0
        normalized_role = PlayerRoles.normalize_role(player.role)
        
        if self.strategy == TeamStrategies.AGGRESSIVE:
            if normalized_role in [PlayerRoles.BATSMAN, PlayerRoles.ALL_ROUNDER]:
                role_multiplier = 1.2
        elif self.strategy == TeamStrategies.DEFENSIVE:
            if normalized_role in [PlayerRoles.BOWLER, PlayerRoles.ALL_ROUNDER]:
                role_multiplier = 1.2
        elif self.strategy == TeamStrategies.ALL_ROUNDERS:
            if normalized_role == PlayerRoles.ALL_ROUNDER:
                role_multiplier = 1.3
        
        # Calculate final score
        final_score = (form_score + credit_score) * role_multiplier
        
        # Apply opposition consideration if enabled
        if self.consider_opposition:
            # This would be more complex in a real implementation
            # For now, we'll just add a small random factor
            opposition_factor = random.uniform(0.9, 1.1)
            final_score *= opposition_factor
        
        return final_score
    
    def select_players(self):
        """Select players for the team based on requirements and constraints"""
        logger.info("Starting player selection process...")
        selected_players = []
        total_credits = 0
        team_counts = {self.match.team1: 0, self.match.team2: 0}
        
        # Get role requirements
        role_requirements = self.get_role_requirements()
        logger.info(f"Role requirements for strategy '{self.strategy}': {role_requirements}")
        
        # Calculate scores for all players once (performance optimization)
        player_scores = {}
        for player in self.team1_players + self.team2_players:
            player_scores[player.id] = self.calculate_player_score(player)
        
        # Pre-sort players by score within each role (performance optimization)
        sorted_players_by_role = {}
        for role, players in self.players_by_role.items():
            sorted_players_by_role[role] = sorted(
                players, 
                key=lambda p: player_scores[p.id], 
                reverse=True
            )
        
        # Log player counts by role for debugging
        for role, players in sorted_players_by_role.items():
            logger.info(f"Found {len(players)} players for role {role}")
            # Log top 3 players for each role to help with debugging
            for i, player in enumerate(players[:3]):
                logger.info(f"  Top player {i+1} for {role}: {player.name}, {player.team_name}, credits: {player.credit_points}, score: {player_scores[player.id]:.2f}")
        
        # Validate if we have enough players for each role before starting
        for role, (min_count, _) in role_requirements.items():
            players_for_role = sorted_players_by_role.get(role, [])
            
            if len(players_for_role) < min_count:
                error_msg = f"Not enough {role} players available to create a valid team. Need {min_count}, have {len(players_for_role)}"
                logger.error(error_msg)
                raise TeamGenerationError(error_msg)
        
        # OPTIMIZATION: Pre-check if it's even possible to create a valid team
        # Check if we have enough players across all roles
        total_available_players = sum(len(players) for players in sorted_players_by_role.values())
        if total_available_players < 11:
            error_msg = f"Not enough players available to create a valid team. Need 11, have {total_available_players}"
            logger.error(error_msg)
            raise TeamGenerationError(error_msg)
            
        # Check if we have enough credits for the cheapest possible team
        all_players = self.team1_players + self.team2_players
        all_players.sort(key=lambda p: p.credit_points)
        min_possible_credits = sum(p.credit_points for p in all_players[:11])
        if min_possible_credits > 100:
            error_msg = f"Cannot create a team within credit limit. Minimum possible team costs {min_possible_credits} credits"
            logger.error(error_msg)
            raise TeamGenerationError(error_msg)
        
        # First, select the minimum required players for each role
        logger.info("Selecting minimum required players for each role...")
        for role, (min_count, _) in role_requirements.items():
            players_for_role = sorted_players_by_role.get(role, [])
            logger.info(f"Selecting {min_count} players for role {role} from {len(players_for_role)} available players")
            
            # OPTIMIZATION: Create a copy of the list to avoid modifying while iterating
            available_players = [p for p in players_for_role if p not in selected_players]
            
            # Select top players for this role
            selected_for_role = 0
            for i in range(min_count):
                # Find the best player that doesn't violate constraints
                best_player = None
                best_player_idx = -1
                best_player_score = -1
                
                for idx, player in enumerate(available_players):
                    # Skip if already selected
                    if player in selected_players:
                        continue
                    
                    # Check constraints
                    if (team_counts[player.team_name] >= self.max_players_from_team or 
                        total_credits + player.credit_points > 100):
                        continue
                    
                    # Found a valid player, check if it's the best so far
                    player_score = player_scores[player.id]
                    if player_score > best_player_score:
                        best_player = player
                        best_player_idx = idx
                        best_player_score = player_score
                
                if best_player:
                    # Add the best player found
                    selected_players.append(best_player)
                    total_credits += best_player.credit_points
                    team_counts[best_player.team_name] += 1
                    selected_for_role += 1
                    logger.info(f"Selected {best_player.name} ({best_player.role}) from {best_player.team_name}, credits: {best_player.credit_points}, total credits: {total_credits}")
                    # Remove from available players
                    available_players.pop(best_player_idx)
                else:
                    # If we get here, we couldn't find a valid player
                    error_msg = f"Couldn't find a valid player for role {role} that meets all constraints"
                    logger.warning(error_msg)
                    
                    # Try with relaxed constraints if we're stuck
                    logger.info("Attempting to relax constraints to find a valid player...")
                    
                    # OPTIMIZATION: Try relaxing constraints in order of importance
                    # 1. Try relaxing team count constraint but keep credit limit
                    relaxed_player = None
                    for p in available_players:
                        if total_credits + p.credit_points <= 100:
                            relaxed_player = p
                            logger.info(f"Found player {p.name} by relaxing team count constraint")
                            break
                    
                    if relaxed_player:
                        selected_players.append(relaxed_player)
                        total_credits += relaxed_player.credit_points
                        team_counts[relaxed_player.team_name] += 1
                        selected_for_role += 1
                        logger.info(f"Selected {relaxed_player.name} with relaxed constraints, total credits: {total_credits}")
                        available_players.remove(relaxed_player)
                    else:
                        # If still can't find a player, raise error with detailed message
                        detailed_error = f"Cannot create a valid team with current constraints. "
                        detailed_error += f"Team counts: {team_counts}, "
                        detailed_error += f"Total credits: {total_credits}, "
                        detailed_error += f"Selected players: {len(selected_players)}"
                        logger.error(detailed_error)
                        raise TeamGenerationError(detailed_error)
            
            logger.info(f"Selected {selected_for_role} players for role {role}")
        
        # Now fill remaining slots to reach 11 players
        remaining_slots = 11 - len(selected_players)
        logger.info(f"Filling {remaining_slots} remaining slots to reach 11 players...")
        
        if remaining_slots > 0:
            # OPTIMIZATION: Create a prioritized pool of remaining players
            # This avoids recalculating available players for each slot
            remaining_pool = []
            
            for role, (_, max_count) in role_requirements.items():
                current_count = sum(1 for p in selected_players if PlayerRoles.normalize_role(p.role) == role)
                can_add = max_count - current_count
                
                if can_add > 0:
                    # Get players not already selected
                    available = [p for p in sorted_players_by_role.get(role, []) 
                               if p not in selected_players]
                    
                    # Add to pool with role info and pre-calculated score
                    for player in available:
                        remaining_pool.append({
                            'player': player,
                            'role': role,
                            'score': player_scores[player.id],
                            'credits': player.credit_points,
                            'team': player.team_name
                        })
            
            # Sort by score (highest first)
            remaining_pool.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"Total remaining player pool size: {len(remaining_pool)}")
            
            # OPTIMIZATION: Use a more efficient algorithm for filling remaining slots
            # Try to fill all slots at once with the best possible players
            for _ in range(remaining_slots):
                # Try with strict constraints first
                best_idx = -1
                for idx, player_info in enumerate(remaining_pool):
                    player = player_info['player']
                    role = player_info['role']
                    
                    # Skip if already selected
                    if player in selected_players:
                        continue
                    
                    # Check all constraints
                    current_role_count = sum(1 for p in selected_players if PlayerRoles.normalize_role(p.role) == role)
                    _, max_role_count = role_requirements[role]
                    
                    if (current_role_count >= max_role_count or
                        team_counts[player.team_name] >= self.max_players_from_team or
                        total_credits + player.credit_points > 100):
                        continue
                    
                    # Found a valid player
                    best_idx = idx
                    break
                
                if best_idx >= 0:
                    # Add the best player found
                    player_info = remaining_pool[best_idx]
                    player = player_info['player']
                    role = player_info['role']
                    
                    selected_players.append(player)
                    total_credits += player.credit_points
                    team_counts[player.team_name] += 1
                    logger.info(f"Selected {player.name} ({role}) from {player.team_name}, credits: {player.credit_points}, total credits: {total_credits}")
                    
                    # Mark as used by removing from pool
                    remaining_pool.pop(best_idx)
                else:
                    # Try with relaxed constraints
                    logger.warning("Couldn't find a player with strict constraints, trying with relaxed constraints...")
                    
                    # OPTIMIZATION: Try different relaxation strategies in order of preference
                    # 1. Relax role constraints but keep team and credit constraints
                    found_player = False
                    for idx, player_info in enumerate(remaining_pool):
                        player = player_info['player']
                        
                        if player in selected_players:
                            continue
                            
                        # Keep team count and credit constraints
                        if (team_counts[player.team_name] >= self.max_players_from_team or
                            total_credits + player.credit_points > 100):
                            continue
                            
                        # Player is valid with relaxed role constraint
                        role = PlayerRoles.normalize_role(player.role)
                        selected_players.append(player)
                        total_credits += player.credit_points
                        team_counts[player.team_name] += 1
                        logger.info(f"Selected {player.name} ({role}) with relaxed role constraints, total credits: {total_credits}")
                        remaining_pool.pop(idx)
                        found_player = True
                        break
                    
                    # 2. If still not found, relax team constraints but keep credit constraint
                    if not found_player:
                        for idx, player_info in enumerate(remaining_pool):
                            player = player_info['player']
                            
                            if player in selected_players:
                                continue
                                
                            # Only keep credit constraint
                            if total_credits + player.credit_points > 100:
                                continue
                                
                            # Player is valid with relaxed team constraint
                            role = PlayerRoles.normalize_role(player.role)
                            selected_players.append(player)
                            total_credits += player.credit_points
                            team_counts[player.team_name] += 1
                            logger.info(f"Selected {player.name} ({role}) with relaxed team constraints, total credits: {total_credits}")
                            remaining_pool.pop(idx)
                            found_player = True
                            break
                    
                    # If still not found, we have a serious problem
                    if not found_player:
                        error_msg = f"Unable to fill team with valid players after trying relaxed constraints. "
                        error_msg += f"Selected {len(selected_players)} of 11 required players. "
                        error_msg += f"Team counts: {team_counts}, Total credits: {total_credits}"
                        logger.error(error_msg)
                        raise TeamGenerationError(error_msg)
        
        # Verify we have exactly 11 players
        if len(selected_players) != 11:
            error_msg = f"Unable to create a valid team with exactly 11 players. Selected {len(selected_players)} players."
            logger.error(error_msg)
            raise TeamGenerationError(error_msg)
        
        # Verify we're within credit limit
        if total_credits > 100:
            error_msg = f"Team exceeds credit limit: {total_credits} > 100"
            logger.error(error_msg)
            raise TeamGenerationError(error_msg)
        
        # Log final team composition
        logger.info(f"Final team composition:")
        role_counts = defaultdict(int)
        for player in selected_players:
            role = PlayerRoles.normalize_role(player.role)
            role_counts[role] += 1
            logger.info(f"  {player.name} ({role}) from {player.team_name}, credits: {player.credit_points}")
        
        logger.info(f"Role distribution: {dict(role_counts)}")
        logger.info(f"Team distribution: {team_counts}")
        logger.info(f"Total credits: {total_credits}")
        
        return selected_players
    
    def select_captain_and_vice_captain(self, selected_players):
        """Select captain and vice-captain based on preferences with enhanced scoring"""
        logger.info("Selecting captain and vice-captain...")
        
        # Enhanced player scoring system for captain selection
        player_scores = {}
        player_details = {}  # Store additional details for logging
        
        for player in selected_players:
            # Get normalized role for consistency
            role = PlayerRoles.normalize_role(player.role)
            
            # Base scores
            form_score = player.current_form
            credit_score = player.credit_points / 10  # Normalize to 0-1 range
            
            # Calculate role-specific bonuses
            role_multipliers = {
                PlayerRoles.BATSMAN: 1.0,
                PlayerRoles.BOWLER: 1.0,
                PlayerRoles.ALL_ROUNDER: 1.2,  # Slight bonus for all-rounders by default
                PlayerRoles.WICKET_KEEPER: 0.9  # Slight penalty for wicket keepers by default
            }
            
            # Apply strategy-specific adjustments
            if self.captain_preference == CaptainPreferences.HIGHEST_POINTS:
                # Prioritize credits (assumed to correlate with points potential)
                base_score = credit_score * 0.7 + form_score * 0.3
                # Bonus for high-credit players
                if player.credit_points > 9.0:
                    base_score *= 1.2
                    
            elif self.captain_preference == CaptainPreferences.BEST_FORM or self.captain_preference == CaptainPreferences.FORM:
                # Prioritize current form
                base_score = form_score * 0.8 + credit_score * 0.2
                # Extra weight for recent form
                if form_score > 0.7:
                    base_score *= 1.3
                    
            elif self.captain_preference == CaptainPreferences.ALL_ROUNDER:
                # Prioritize all-rounders
                role_multipliers[PlayerRoles.ALL_ROUNDER] = 1.8  # Significant bonus
                base_score = form_score * 0.5 + credit_score * 0.5
                
            elif self.captain_preference == CaptainPreferences.BATSMAN:
                # Prioritize batsmen
                role_multipliers[PlayerRoles.BATSMAN] = 1.7  # Significant bonus
                role_multipliers[PlayerRoles.ALL_ROUNDER] = 1.3  # Moderate bonus
                base_score = form_score * 0.5 + credit_score * 0.5
                
            elif self.captain_preference == CaptainPreferences.BOWLER:
                # Prioritize bowlers
                role_multipliers[PlayerRoles.BOWLER] = 1.7  # Significant bonus
                role_multipliers[PlayerRoles.ALL_ROUNDER] = 1.3  # Moderate bonus
                base_score = form_score * 0.5 + credit_score * 0.5
                
            else:
                # Default to balanced approach
                base_score = form_score * 0.5 + credit_score * 0.5
            
            # Apply role multiplier
            final_score = base_score * role_multipliers.get(role, 1.0)
            
            # Store score and details for logging
            player_scores[player.id] = final_score
            player_details[player.id] = {
                'name': player.name,
                'role': role,
                'team': player.team_name,
                'credits': player.credit_points,
                'form': player.current_form,
                'score': final_score
            }
        
        # Sort players by score
        sorted_players = sorted(selected_players, key=lambda p: player_scores[p.id], reverse=True)
        
        # Log top candidates for captain
        logger.info("Top captain candidates:")
        for i, player in enumerate(sorted_players[:3]):
            details = player_details[player.id]
            logger.info(f"  {i+1}. {details['name']} ({details['role']}) - Score: {details['score']:.2f}, Credits: {details['credits']}, Form: {details['form']:.2f}")
        
        # Select captain (highest score)
        captain = sorted_players[0]
        logger.info(f"Selected captain: {player_details[captain.id]['name']} ({player_details[captain.id]['role']})")
        
        # For vice-captain, implement enhanced selection logic
        vice_captain = None
        
        if self.vice_captain_preference == CaptainPreferences.SECOND_HIGHEST_POINTS:
            # Simply take the second highest scoring player
            vice_captain = sorted_players[1]
            
        elif self.vice_captain_preference == CaptainPreferences.DIFFERENT_TEAM:
            # Try to select a player from a different team than the captain
            captain_team = captain.team_name
            
            # Find highest scoring player from different team
            different_team_players = [p for p in sorted_players[1:] if p.team_name != captain_team]
            if different_team_players:
                vice_captain = different_team_players[0]  # Highest scoring from different team
            else:
                # If all players are from the same team, take the second highest overall
                vice_captain = sorted_players[1]
                logger.info("All players are from the same team, selecting second highest scoring player")
                
        elif self.vice_captain_preference == CaptainPreferences.DIFFERENT_ROLE:
            # Try to select a player with a different role than the captain
            captain_role = PlayerRoles.normalize_role(captain.role)
            
            # Find highest scoring player with different role
            different_role_players = [p for p in sorted_players[1:] 
                                     if PlayerRoles.normalize_role(p.role) != captain_role]
            if different_role_players:
                vice_captain = different_role_players[0]  # Highest scoring with different role
            else:
                # If all players have the same role, take the second highest overall
                vice_captain = sorted_players[1]
                logger.info("All remaining players have the same role, selecting second highest scoring player")
        else:
            # Default to second highest scoring player
            vice_captain = sorted_players[1]
        
        logger.info(f"Selected vice-captain: {player_details[vice_captain.id]['name']} ({player_details[vice_captain.id]['role']})")
        
        # Verify selections are different players
        if captain.id == vice_captain.id:
            logger.error("Captain and vice-captain are the same player! Selecting different vice-captain.")
            # Ensure we select a different player
            for player in sorted_players:
                if player.id != captain.id:
                    vice_captain = player
                    logger.info(f"Corrected vice-captain: {player_details[vice_captain.id]['name']}")
                    break
        
        return captain, vice_captain
    
    def generate_team(self):
        """Generate a complete team based on all parameters and constraints"""
        try:
            # Log team generation attempt
            logger.info(f"Generating team for match {self.match_id}, user {self.user_id} with strategy {self.strategy}")
            logger.info(f"Team generation parameters: max_players_from_team={self.max_players_from_team}, form_weight={self.form_weight}, credit_weight={self.credit_weight}")
            
            # Verify match exists and has valid data
            if not self.match:
                error_msg = f"Match with ID {self.match_id} not found or is invalid"
                logger.error(error_msg)
                return None, error_msg
                
            # Verify we have enough players for both teams
            if len(self.team1_players) < 11:
                error_msg = f"Not enough players for team {self.match.team1}. Found {len(self.team1_players)}, need at least 11"
                logger.error(error_msg)
                return None, error_msg
                
            if len(self.team2_players) < 11:
                error_msg = f"Not enough players for team {self.match.team2}. Found {len(self.team2_players)}, need at least 11"
                logger.error(error_msg)
                return None, error_msg
            
            # Validate player roles
            role_counts = {}
            for player in self.team1_players + self.team2_players:
                normalized_role = PlayerRoles.normalize_role(player.role)
                role_counts[normalized_role] = role_counts.get(normalized_role, 0) + 1
            
            logger.info(f"Player role distribution: {role_counts}")
            
            # Check if we have enough players for each role
            min_required = {
                PlayerRoles.BATSMAN: 4,
                PlayerRoles.BOWLER: 4,
                PlayerRoles.ALL_ROUNDER: 2,
                PlayerRoles.WICKET_KEEPER: 1
            }
            
            missing_roles = []
            for role, min_count in min_required.items():
                if role_counts.get(role, 0) < min_count:
                    missing_roles.append(f"{role} (have {role_counts.get(role, 0)}, need {min_count})")
            
            if missing_roles:
                error_msg = f"Insufficient players for required roles: {', '.join(missing_roles)}"
                logger.error(error_msg)
                return None, error_msg
            
            # Select players
            logger.info("Calling select_players method...")
            try:
                selected_players = self.select_players()
                logger.info(f"Successfully selected {len(selected_players)} players for team")
            except TeamGenerationError as e:
                logger.error(f"Error selecting players: {str(e)}")
                return None, str(e)
            except Exception as e:
                logger.error(f"Unexpected error during player selection: {str(e)}", exc_info=True)
                return None, f"Unexpected error during player selection: {str(e)}"
            
            if not selected_players:
                error_msg = "No players were selected"
                logger.error(error_msg)
                return None, error_msg
                
            if len(selected_players) != 11:
                error_msg = f"Failed to select exactly 11 players. Got {len(selected_players)} players."
                logger.error(error_msg)
                return None, error_msg
            
            # Verify team composition
            selected_role_counts = {}
            for player in selected_players:
                normalized_role = PlayerRoles.normalize_role(player.role)
                selected_role_counts[normalized_role] = selected_role_counts.get(normalized_role, 0) + 1
            
            logger.info(f"Selected team composition: {selected_role_counts}")
            
            # Verify team credits
            total_credits = sum(p.credit_points for p in selected_players)
            if total_credits > 100:
                error_msg = f"Team exceeds credit limit: {total_credits} > 100"
                logger.error(error_msg)
                return None, error_msg
            
            logger.info(f"Team total credits: {total_credits}")
            
            # Select captain and vice-captain
            try:
                captain, vice_captain = self.select_captain_and_vice_captain(selected_players)
                logger.info(f"Selected captain: {captain.name}, vice-captain: {vice_captain.name}")
            except Exception as e:
                logger.error(f"Error selecting captain/vice-captain: {str(e)}")
                return None, f"Error selecting captain/vice-captain: {str(e)}"
            
            # Create team in database
            try:
                team = Team(
                    name=self.team_name,
                    user_id=self.user_id,
                    match_id=self.match_id,
                    captain_id=captain.id,
                    vice_captain_id=vice_captain.id
                )
                self.db.session.add(team)
                self.db.session.flush()  # Get the team ID without committing
                
                # Add player selections
                for player in selected_players:
                    team_player = TeamPlayer(
                        team_id=team.id,
                        player_id=player.id,
                        is_captain=player.id == captain.id,
                        is_vice_captain=player.id == vice_captain.id
                    )
                    self.db.session.add(team_player)
                
                self.db.session.commit()
                logger.info(f"Successfully generated team {team.id} for match {self.match_id} with strategy {self.strategy}")
                
                # Log team details for debugging
                team_details = {
                    'id': team.id,
                    'match': f"{self.match.team1_short_name} vs {self.match.team2_short_name}",
                    'strategy': self.strategy,
                    'captain': captain.name,
                    'vice_captain': vice_captain.name,
                    'total_credits': total_credits,
                    'composition': selected_role_counts
                }
                logger.info(f"Team details: {team_details}")
                
                return team, None
            except Exception as e:
                self.db.session.rollback()
                logger.error(f"Database error while creating team: {str(e)}", exc_info=True)
                return None, f"Database error while creating team: {traceback.format_exc()}"
            
        except TeamGenerationError as e:
            # Already logged and formatted, just rollback and re-raise
            try:
                self.db.session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {str(rollback_error)}")
            raise
            
        except SQLAlchemyError as e:
            # Database error
            logger.error(f"Database error during team generation: {str(e)}", exc_info=True)
            try:
                self.db.session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {str(rollback_error)}")
            raise TeamGenerationError(f"Database error during team generation: {str(e)}")
            
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error generating team: {str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            try:
                self.db.session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {str(rollback_error)}")
            raise TeamGenerationError(f"Unexpected error during team generation: {str(e)}")
            
def generate_auto_team(match_id, user_id, db, **kwargs):
    """
    Generate a team automatically based on parameters.
    Returns a tuple (team, error_message). If successful, team is the Team object and error_message is None.
    If failed, team is None and error_message contains the reason.
    """
    logger.info(f"Attempting to generate auto team for match_id={match_id}, user_id={user_id}")
    logger.debug(f"Auto-generate kwargs: {kwargs}")
    
    # Validate input parameters first
    try:
        # Ensure match_id and user_id are valid integers
        try:
            match_id = int(match_id)
            user_id = int(user_id)
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid parameters: match_id or user_id is not a valid integer. Details: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
            
        # Verify database connection
        if not db or not hasattr(db, 'session'):
            error_msg = "Invalid database connection"
            logger.error(error_msg)
            return None, error_msg
            
        # Verify match exists
        from src.models.match import Match
        match = db.session.query(Match).filter_by(id=match_id).first()
        if not match:
            error_msg = f"Match with ID {match_id} not found"
            logger.error(error_msg)
            return None, error_msg
            
        # Verify user exists
        from src.models.user import User
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            error_msg = f"User with ID {user_id} not found"
            logger.error(error_msg)
            return None, error_msg
            
        # Validate strategy parameter if provided
        from src.utils.constants import TeamStrategies
        if 'strategy' in kwargs and kwargs['strategy'] not in TeamStrategies.get_all_strategies():
            error_msg = f"Invalid strategy: {kwargs.get('strategy')}. Valid options are: {', '.join(TeamStrategies.get_all_strategies())}"
            logger.error(error_msg)
            return None, error_msg
            
        # Initialize the team generator
        logger.info("Initializing TeamGenerator...")
        try:
            generator = TeamGenerator(match_id, user_id, db, **kwargs)
            logger.info("TeamGenerator initialized successfully.")
        except TeamGenerationError as e:
            error_msg = f"Error initializing team generator: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during initialization: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
        
        # Generate the team - properly handle tuple return value
        logger.info("Starting team generation process...")
        try:
            # The generate_team method returns a tuple (team, error_message)
            team, error_msg = generator.generate_team()
            
            if team:
                logger.info(f"Team generated successfully with ID: {team.id}")
                return team, None
            else:
                # If team is None, error_msg should contain the reason
                if not error_msg:
                    error_msg = "Team generation failed without specific error message"
                logger.error(f"Team generation failed: {error_msg}")
                return None, error_msg
                
        except TeamGenerationError as e:
            error_msg = f"Error generating team: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except SQLAlchemyError as e:
            error_msg = f"Database error during team generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during team generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
            
    except Exception as e:
        # Catch-all for any other unexpected errors
        error_msg = f"Unexpected error in generate_auto_team: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg
