"""
Slots game API views.
"""
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from games.services.slots_service import SlotsGameService
from wallet.services import InsufficientFundsError


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_game(request):
    """
    Create and play a slots game.
    
    POST /api/games/slots/create/
    Body: {
        "bet_amount": "10.00",
        "reels_count": 5,
        "client_seed": "optional_seed"
    }
    """
    try:
        # Parse request body
        data = json.loads(request.body)
        
        # Extract parameters
        bet_amount = Decimal(str(data.get('bet_amount', 0)))
        reels_count = int(data.get('reels_count', 5))
        client_seed = data.get('client_seed')
        
        # Create and play game
        game = SlotsGameService.create_and_play_game(
            user=request.user,
            bet_amount=bet_amount,
            reels_count=reels_count,
            client_seed=client_seed
        )
        
        # Get updated balance
        balance = request.user.profile.balance
        
        return JsonResponse({
            'success': True,
            'data': {
                'game_id': game.id,
                'bet_amount': str(game.bet_amount),
                'reels_count': game.reels_count,
                'reels': game.reels,
                'multiplier': str(game.multiplier),
                'win_amount': str(game.win_amount),
                'winning_combination': game.winning_combination,
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
    """Get user's slots game history."""
    try:
        # Get limit parameter
        limit = int(request.GET.get('limit', 10))
        limit = min(max(limit, 1), 100)
        
        # Get games
        games = SlotsGameService.get_user_games(request.user, limit=limit)
        
        # Format response
        games_data = []
        for game in games:
            games_data.append({
                'game_id': game.id,
                'bet_amount': str(game.bet_amount),
                'reels_count': game.reels_count,
                'reels': game.reels,
                'multiplier': str(game.multiplier),
                'win_amount': str(game.win_amount),
                'winning_combination': game.winning_combination,
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
    """Get specific slots game details."""
    try:
        # Get game
        game = SlotsGameService.get_game_by_id(game_id, user=request.user)
        
        if not game:
            return JsonResponse({
                'success': False,
                'error': 'Игра не найдена'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'data': {
                'game_id': game.id,
                'bet_amount': str(game.bet_amount),
                'reels_count': game.reels_count,
                'reels': game.reels,
                'multiplier': str(game.multiplier),
                'win_amount': str(game.win_amount),
                'winning_combination': game.winning_combination,
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
            'error': 'Произошла ошибку при получении игры'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_game(request):
    """Verify slots game result using provably fair."""
    try:
        # Parse request body
        data = json.loads(request.body)
        game_id = int(data.get('game_id', 0))
        
        # Get game
        game = SlotsGameService.get_game_by_id(game_id)
        
        if not game:
            return JsonResponse({
                'success': False,
                'error': 'Игра не найдена'
            }, status=404)
        
        # Verify game
        is_valid = SlotsGameService.verify_game(game)
        
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
