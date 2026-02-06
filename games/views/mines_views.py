"""
Mines game API views.
All views use MinesGameService for business logic (SRP).
"""
import logging
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from games.models import MinesGame
from games.services.mines_service import MinesGameService
from wallet.services import InsufficientFundsError

logger = logging.getLogger('games')


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_mines_game(request):
    """
    Create new Mines game.
    
    POST /api/games/mines/create/
    
    Request Body:
        {
            "bet_amount": "10.00",
            "mine_count": 5,
            "client_seed": "optional_custom_seed"
        }
    
    Response:
        200: {
            "success": true,
            "game_id": 123,
            "bet_amount": "10.00",
            "mine_count": 5,
            "server_seed_hash": "abc123...",
            "client_seed": "def456...",
            "nonce": 0,
            "current_multiplier": "1.00",
            "grid_size": 5
        }
        400: {"error": "Ошибка валидации"}
        401: {"error": "Требуется авторизация"}
    """
    try:
        # Parse request body
        data = json.loads(request.body)
        
        bet_amount = Decimal(str(data.get('bet_amount')))
        mine_count = int(data.get('mine_count'))
        client_seed = data.get('client_seed', None)
        
        # Create game
        game = MinesGameService.create_game(
            user=request.user,
            bet_amount=bet_amount,
            mine_count=mine_count,
            client_seed=client_seed
        )
        
        logger.info(
            f"Mines game created via API: id={game.id}, "
            f"user={request.user.username}"
        )
        
        # Get updated balance
        request.user.profile.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'game_id': game.id,
            'bet_amount': str(game.bet_amount),
            'mine_count': game.mine_count,
            'server_seed_hash': game.server_seed_hash,
            'client_seed': game.client_seed,
            'nonce': game.nonce,
            'current_multiplier': str(game.current_multiplier),
            'grid_size': MinesGameService.GRID_SIZE,
            'state': game.state,
            'new_balance': str(request.user.profile.balance)
        }, status=201)
        
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        logger.error(f"Invalid request data: {e}")
        return JsonResponse({
            'error': 'Неверный формат данных'
        }, status=400)
    
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=400)
    
    except InsufficientFundsError as e:
        logger.error(f"Insufficient funds: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error in create_mines_game: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def open_cell(request, game_id):
    """
    Open a cell in Mines game.
    
    POST /api/games/mines/<game_id>/open/
    
    Request Body:
        {
            "cell_index": 12
        }
        OR
        {
            "row": 2,
            "col": 3
        }
    
    Response:
        200: {
            "hit_mine": false,
            "current_multiplier": "1.25",
            "opened_count": 1
        }
        
        OR (if mine hit):
        
        200: {
            "hit_mine": true,
            "mine_positions": [0, 5, 12, ...],
            "verification": {...}
        }
        
        400: {"error": "Ошибка валидации"}
        404: {"error": "Игра не найдена"}
    """
    try:
        # Get game
        game = MinesGame.objects.get(id=game_id, user=request.user)
        
        # Parse request body
        data = json.loads(request.body)
        
        # Support both cell_index and row/col formats
        if 'cell_index' in data:
            cell_index = int(data.get('cell_index'))
            row = cell_index // 5
            col = cell_index % 5
        else:
            row = int(data.get('row'))
            col = int(data.get('col'))
        
        # Open cell
        result = MinesGameService.open_cell(game, row, col)
        
        logger.info(
            f"Cell opened in game {game_id}: ({row}, {col}), "
            f"is_mine={result['is_mine']}"
        )
        
        # Format response
        if result['is_mine']:
            # Game lost - convert mine positions to cell indices
            mine_indices = [pos[0] * 5 + pos[1] for pos in result['mine_positions']]
            response = {
                'hit_mine': True,
                'mine_positions': mine_indices,
                'verification': {
                    'server_seed': result['server_seed'],
                    'server_seed_hash': result['server_seed_hash'],
                    'client_seed': result['client_seed'],
                    'nonce': result['nonce']
                }
            }
        else:
            # Safe cell
            response = {
                'hit_mine': False,
                'current_multiplier': float(result['multiplier']),
                'opened_count': result['opened_count']
            }
        
        return JsonResponse(response, status=200)
        
    except MinesGame.DoesNotExist:
        logger.error(f"Game {game_id} not found for user {request.user.username}")
        return JsonResponse({
            'error': 'Игра не найдена'
        }, status=404)
    
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        logger.error(f"Invalid request data: {e}")
        return JsonResponse({
            'error': 'Неверный формат данных'
        }, status=400)
    
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error in open_cell: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def cashout_game(request, game_id):
    """
    Cash out Mines game.
    
    POST /api/games/mines/<game_id>/cashout/
    
    Response:
        200: {
            "success": true,
            "winnings": "12.50",
            "multiplier": "1.25",
            "game_state": "cashed_out",
            "mine_positions": [[0, 0], [1, 1], ...],
            "verification": {
                "server_seed": "abc123...",
                "server_seed_hash": "def456...",
                "client_seed": "ghi789...",
                "nonce": 0
            }
        }
        400: {"error": "Ошибка валидации"}
        404: {"error": "Игра не найдена"}
    """
    try:
        # Get game
        game = MinesGame.objects.get(id=game_id, user=request.user)
        
        # Cashout
        winnings = MinesGameService.cashout(game)
        
        logger.info(
            f"Game {game_id} cashed out: winnings={winnings}, "
            f"multiplier={game.current_multiplier}x"
        )
        
        # Refresh game and user profile from database
        game.refresh_from_db()
        request.user.profile.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'winnings': str(winnings),
            'multiplier': str(game.current_multiplier),
            'game_state': game.state,
            'new_balance': str(request.user.profile.balance),
            'mine_positions': game.mine_positions,
            'verification': {
                'server_seed': game.server_seed,
                'server_seed_hash': game.server_seed_hash,
                'client_seed': game.client_seed,
                'nonce': game.nonce
            }
        }, status=200)
        
    except MinesGame.DoesNotExist:
        logger.error(f"Game {game_id} not found for user {request.user.username}")
        return JsonResponse({
            'error': 'Игра не найдена'
        }, status=404)
    
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error in cashout_game: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_game(request, game_id):
    """
    Get Mines game details.
    
    GET /api/games/mines/<game_id>/
    
    Response:
        200: {
            "game_id": 123,
            "bet_amount": "10.00",
            "mine_count": 5,
            "state": "active",
            "current_multiplier": "1.25",
            "opened_cells": [[2, 3]],
            "opened_count": 1,
            "server_seed_hash": "abc123...",
            "client_seed": "def456...",
            "nonce": 0,
            "created_at": "2024-01-15T10:30:00Z",
            "ended_at": null
        }
        404: {"error": "Игра не найдена"}
    """
    try:
        # Get game
        game = MinesGame.objects.get(id=game_id, user=request.user)
        
        response = {
            'game_id': game.id,
            'bet_amount': str(game.bet_amount),
            'mine_count': game.mine_count,
            'state': game.state,
            'current_multiplier': str(game.current_multiplier),
            'opened_cells': game.opened_cells,
            'opened_count': game.get_opened_cells_count(),
            'server_seed_hash': game.server_seed_hash,
            'client_seed': game.client_seed,
            'nonce': game.nonce,
            'created_at': game.created_at.isoformat(),
            'ended_at': game.ended_at.isoformat() if game.ended_at else None
        }
        
        # Include mine positions if game ended
        if game.is_ended():
            response['mine_positions'] = game.mine_positions
        
        return JsonResponse(response, status=200)
        
    except MinesGame.DoesNotExist:
        logger.error(f"Game {game_id} not found for user {request.user.username}")
        return JsonResponse({
            'error': 'Игра не найдена'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Unexpected error in get_game: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def verify_game(request, game_id):
    """
    Get provably fair verification data.
    
    GET /api/games/mines/<game_id>/verify/
    
    Response:
        200: {
            "server_seed": "abc123...",
            "server_seed_hash": "def456...",
            "client_seed": "ghi789...",
            "nonce": 0,
            "mine_count": 5,
            "mine_positions": [[0, 0], [1, 1], ...],
            "is_valid": true
        }
        400: {"error": "Игра еще не завершена"}
        404: {"error": "Игра не найдена"}
    """
    try:
        # Get game
        game = MinesGame.objects.get(id=game_id, user=request.user)
        
        # Get verification data
        verification_data = MinesGameService.get_verification_data(game)
        
        return JsonResponse(verification_data, status=200)
        
    except MinesGame.DoesNotExist:
        logger.error(f"Game {game_id} not found for user {request.user.username}")
        return JsonResponse({
            'error': 'Игра не найдена'
        }, status=404)
    
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error in verify_game: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)
