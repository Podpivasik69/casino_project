"""
Dice game API views.
"""
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from games.services.dice_service import DiceGameService
from wallet.services import InsufficientFundsError


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_game(request):
    """
    Create and play a dice game.
    
    POST /api/games/dice/create/
    Body: {
        "bet_amount": "10.00",
        "selected_number": 3,
        "client_seed": "optional_seed"
    }
    
    Returns:
        {
            "success": true,
            "data": {
                "game_id": 123,
                "bet_amount": "10.00",
                "selected_number": 3,
                "rolled_number": 5,
                "multiplier": "0.00",
                "won": false,
                "winnings": "0.00",
                "balance": "90.00",
                "server_seed_hash": "abc123...",
                "client_seed": "def456...",
                "nonce": 0,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    """
    try:
        # Parse request body
        data = json.loads(request.body)
        
        # Extract parameters
        bet_amount = Decimal(str(data.get('bet_amount', 0)))
        selected_number = int(data.get('selected_number', 0))
        client_seed = data.get('client_seed')
        
        # Create and play game
        game = DiceGameService.create_and_play_game(
            user=request.user,
            bet_amount=bet_amount,
            selected_number=selected_number,
            client_seed=client_seed
        )
        
        # Calculate winnings
        winnings = game.bet_amount * game.multiplier if game.won else Decimal('0.00')
        
        # Get updated balance
        balance = request.user.profile.balance
        
        return JsonResponse({
            'success': True,
            'data': {
                'game_id': game.id,
                'bet_amount': str(game.bet_amount),
                'selected_number': game.selected_number,
                'rolled_number': game.rolled_number,
                'multiplier': str(game.multiplier),
                'won': game.won,
                'winnings': str(winnings),
                'balance': str(balance),
                'server_seed_hash': game.server_seed_hash,
                'client_seed': game.client_seed,
                'nonce': game.nonce,
                'created_at': game.created_at.isoformat()
            }
        })
        
    except (ValueError, InvalidOperation, KeyError, TypeError, InsufficientFundsError) as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при создании игры'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_history(request):
    """
    Get user's dice game history.
    
    GET /api/games/dice/history/?limit=10
    
    Returns:
        {
            "success": true,
            "data": {
                "games": [
                    {
                        "game_id": 123,
                        "bet_amount": "10.00",
                        "selected_number": 3,
                        "rolled_number": 5,
                        "multiplier": "0.00",
                        "won": false,
                        "winnings": "0.00",
                        "created_at": "2024-01-01T12:00:00Z"
                    },
                    ...
                ],
                "total": 10
            }
        }
    """
    try:
        # Get limit parameter
        limit = int(request.GET.get('limit', 10))
        limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
        
        # Get games
        games = DiceGameService.get_user_games(request.user, limit=limit)
        
        # Format response
        games_data = []
        for game in games:
            winnings = game.bet_amount * game.multiplier if game.won else Decimal('0.00')
            games_data.append({
                'game_id': game.id,
                'bet_amount': str(game.bet_amount),
                'selected_number': game.selected_number,
                'rolled_number': game.rolled_number,
                'multiplier': str(game.multiplier),
                'won': game.won,
                'winnings': str(winnings),
                'created_at': game.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'games': games_data,
                'total': len(games_data)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при получении истории'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_game(request, game_id):
    """
    Get specific dice game details.
    
    GET /api/games/dice/<game_id>/
    
    Returns:
        {
            "success": true,
            "data": {
                "game_id": 123,
                "bet_amount": "10.00",
                "selected_number": 3,
                "rolled_number": 5,
                "multiplier": "0.00",
                "won": false,
                "winnings": "0.00",
                "server_seed": "abc123...",
                "server_seed_hash": "def456...",
                "client_seed": "ghi789...",
                "nonce": 0,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    """
    try:
        # Get game
        game = DiceGameService.get_game_by_id(game_id, user=request.user)
        
        if not game:
            return JsonResponse({
                'success': False,
                'error': 'Игра не найдена'
            }, status=404)
        
        # Calculate winnings
        winnings = game.bet_amount * game.multiplier if game.won else Decimal('0.00')
        
        return JsonResponse({
            'success': True,
            'data': {
                'game_id': game.id,
                'bet_amount': str(game.bet_amount),
                'selected_number': game.selected_number,
                'rolled_number': game.rolled_number,
                'multiplier': str(game.multiplier),
                'won': game.won,
                'winnings': str(winnings),
                'server_seed': game.server_seed,
                'server_seed_hash': game.server_seed_hash,
                'client_seed': game.client_seed,
                'nonce': game.nonce,
                'created_at': game.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при получении игры'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_game(request):
    """
    Verify dice game result using provably fair.
    
    POST /api/games/dice/verify/
    Body: {
        "game_id": 123
    }
    
    Returns:
        {
            "success": true,
            "data": {
                "game_id": 123,
                "is_valid": true,
                "message": "Игра прошла проверку"
            }
        }
    """
    try:
        # Parse request body
        data = json.loads(request.body)
        game_id = int(data.get('game_id', 0))
        
        # Get game
        game = DiceGameService.get_game_by_id(game_id)
        
        if not game:
            return JsonResponse({
                'success': False,
                'error': 'Игра не найдена'
            }, status=404)
        
        # Verify game
        is_valid = DiceGameService.verify_game(game)
        
        return JsonResponse({
            'success': True,
            'data': {
                'game_id': game.id,
                'is_valid': is_valid,
                'message': 'Игра прошла проверку' if is_valid else 'Игра не прошла проверку'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при проверке игры'
        }, status=500)
