"""
Plinko Game API Views.
"""
import logging
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from games.models import PlinkoGame
from games.services.plinko_service import PlinkoGameService
from wallet.services import InsufficientFundsError

logger = logging.getLogger('games')


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_plinko_game(request):
    """
    Create new Plinko game.
    
    POST /api/games/plinko/create/
    
    Request body:
    {
        "bet_amount": "10.00",
        "row_count": 14,
        "risk_level": "medium"
    }
    
    Response:
    {
        "success": true,
        "game": {
            "id": 1,
            "bet_amount": "10.00",
            "row_count": 14,
            "risk_level": "medium",
            "created_at": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        import json
        data = json.loads(request.body)
        
        bet_amount = Decimal(str(data.get('bet_amount')))
        row_count = int(data.get('row_count'))
        risk_level = data.get('risk_level')
        
        # Create game
        game = PlinkoGameService.create_game(
            user=request.user,
            bet_amount=bet_amount,
            row_count=row_count,
            risk_level=risk_level
        )
        
        return JsonResponse({
            'success': True,
            'game': {
                'id': game.id,
                'bet_amount': str(game.bet_amount),
                'row_count': game.row_count,
                'risk_level': game.risk_level,
                'risk_level_display': game.get_risk_level_display(),
                'created_at': game.created_at.isoformat()
            }
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating Plinko game: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Ошибка при создании игры'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def drop_ball(request, game_id):
    """
    Drop ball in Plinko game.
    
    POST /api/games/plinko/<game_id>/drop/
    
    Response:
    {
        "success": true,
        "result": {
            "ball_path": [0, 1, 1, 0, ...],
            "bucket_index": 7,
            "multiplier": "2.50",
            "winnings": "25.00"
        },
        "balance": "125.00"
    }
    """
    try:
        # Get game
        game = PlinkoGame.objects.get(id=game_id, user=request.user)
        
        # Drop ball
        result = PlinkoGameService.drop_ball(game)
        
        # Get updated balance
        from wallet.services import WalletService
        balance = WalletService.get_balance(request.user)
        
        return JsonResponse({
            'success': True,
            'result': {
                'ball_path': result['ball_path'],
                'bucket_index': result['bucket_index'],
                'multiplier': str(result['multiplier']),
                'winnings': str(result['winnings'])
            },
            'balance': str(balance)
        })
        
    except PlinkoGame.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Игра не найдена'
        }, status=404)
    except InsufficientFundsError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error dropping ball: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Ошибка при броске шарика'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def auto_play(request):
    """
    Auto-play Plinko game (multiple drops).
    
    POST /api/games/plinko/auto/
    
    Request body:
    {
        "bet_amount": "10.00",
        "row_count": 14,
        "risk_level": "medium",
        "drop_count": 10
    }
    
    Response:
    {
        "success": true,
        "results": [
            {
                "game_id": 1,
                "drop_number": 1,
                "ball_path": [...],
                "bucket_index": 7,
                "multiplier": "2.50",
                "winnings": "25.00"
            },
            ...
        ],
        "total_drops": 10,
        "total_winnings": "150.00",
        "balance": "250.00"
    }
    """
    try:
        import json
        data = json.loads(request.body)
        
        bet_amount = Decimal(str(data.get('bet_amount')))
        row_count = int(data.get('row_count'))
        risk_level = data.get('risk_level')
        drop_count = int(data.get('drop_count'))
        
        # Execute auto-play
        results = PlinkoGameService.auto_play(
            user=request.user,
            bet_amount=bet_amount,
            row_count=row_count,
            risk_level=risk_level,
            drop_count=drop_count
        )
        
        # Calculate total winnings
        total_winnings = sum(r['winnings'] for r in results)
        
        # Get updated balance
        from wallet.services import WalletService
        balance = WalletService.get_balance(request.user)
        
        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                'game_id': r['game_id'],
                'drop_number': r['drop_number'],
                'ball_path': r['ball_path'],
                'bucket_index': r['bucket_index'],
                'multiplier': str(r['multiplier']),
                'winnings': str(r['winnings'])
            })
        
        return JsonResponse({
            'success': True,
            'results': formatted_results,
            'total_drops': len(results),
            'total_winnings': str(total_winnings),
            'balance': str(balance)
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error in auto-play: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Ошибка при автоигре'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_plinko_game(request, game_id):
    """
    Get Plinko game details.
    
    GET /api/games/plinko/<game_id>/
    
    Response:
    {
        "success": true,
        "game": {
            "id": 1,
            "bet_amount": "10.00",
            "row_count": 14,
            "risk_level": "medium",
            "ball_path": [...],
            "bucket_index": 7,
            "final_multiplier": "2.50",
            "created_at": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        game = PlinkoGame.objects.get(id=game_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'game': {
                'id': game.id,
                'bet_amount': str(game.bet_amount),
                'row_count': game.row_count,
                'risk_level': game.risk_level,
                'risk_level_display': game.get_risk_level_display(),
                'ball_path': game.ball_path,
                'bucket_index': game.bucket_index,
                'final_multiplier': str(game.final_multiplier) if game.final_multiplier else None,
                'is_completed': game.is_completed(),
                'created_at': game.created_at.isoformat()
            }
        })
        
    except PlinkoGame.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Игра не найдена'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting Plinko game: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Ошибка при получении игры'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_multipliers(request):
    """
    Get multiplier tables for all risk levels and row counts.
    
    GET /api/games/plinko/multipliers/
    
    Response:
    {
        "success": true,
        "multipliers": {
            "low": {
                "12": [8.4, 4.2, ...],
                ...
            },
            ...
        }
    }
    """
    try:
        return JsonResponse({
            'success': True,
            'multipliers': PlinkoGameService.MULTIPLIERS
        })
    except Exception as e:
        logger.error(f"Error getting multipliers: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Ошибка при получении множителей'
        }, status=500)
