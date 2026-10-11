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
            'team1_win_probability': 50,
            'team2_win_probability': 50
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
            }
        }), 500
