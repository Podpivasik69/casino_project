"""
Crash game API views.
"""
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils import timezone
from games.services.crash_service import CrashGameService, InsufficientFundsError


@require_http_methods(["GET"])
@login_required
def current_round(request):
    """
    GET /api/games/crash/current/
    
    Get current round information and multiplier.
    
    Returns:
        - WAITING: status, next_round_at, seconds_until_start
        - ACTIVE: status, current_multiplier, started_at, user_bets
        - CRASHED: status, crash_point, crashed_at, next_round_at
    """
    try:
        round_instance = CrashGameService.get_current_round()
        
        if not round_instance:
            return JsonResponse({
                'error': 'Нет активного раунда'
            }, status=404)
        
        # Base response
        response_data = {
            'round_id': str(round_instance.round_id),
            'status': round_instance.status,
        }
        
        # WAITING state
        if round_instance.is_waiting():
            if round_instance.next_round_at:
                seconds_until_start = (round_instance.next_round_at - timezone.now()).total_seconds()
                response_data.update({
                    'next_round_at': round_instance.next_round_at.isoformat(),
                    'seconds_until_start': max(0, int(seconds_until_start))
                })
        
        # ACTIVE state
        elif round_instance.is_active():
            current_multiplier = CrashGameService.get_current_multiplier(round_instance)
            
            # Get user's bets
            user_bets = CrashGameService.get_user_bets(request.user, round_instance)
            bets_data = []
            
            for bet in user_bets:
                bet_data = {
                    'id': bet.id,
                    'bet_amount': str(bet.bet_amount),
                    'status': bet.status,
                }
                
                if bet.is_active():
                    potential_win = bet.bet_amount * current_multiplier
                    bet_data['potential_win'] = str(potential_win)
                    if bet.auto_cashout_target:
                        bet_data['auto_cashout_target'] = str(bet.auto_cashout_target)
                elif bet.is_cashed_out():
                    bet_data['cashout_multiplier'] = str(bet.cashout_multiplier)
                    bet_data['win_amount'] = str(bet.win_amount)
                
                bets_data.append(bet_data)
            
            response_data.update({
                'current_multiplier': str(current_multiplier),
                'started_at': round_instance.started_at.isoformat(),
                'user_bets': bets_data
            })
        
        # CRASHED state
        elif round_instance.is_crashed():
            response_data.update({
                'crash_point': str(round_instance.crash_point),
                'crashed_at': round_instance.crashed_at.isoformat() if round_instance.crashed_at else None,
            })
            
            # Check if there's a next round
            next_round = CrashGameService.get_current_round()
            if next_round and next_round.is_waiting():
                response_data['next_round_at'] = next_round.next_round_at.isoformat() if next_round.next_round_at else None
        
        return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def place_bet(request):
    """
    POST /api/games/crash/bet/
    
    Place a bet in the current round.
    
    Request body:
        - amount: Bet amount (required)
        - auto_cashout_target: Auto cashout multiplier (optional)
    
    Returns:
        - bet_id, round_id, bet_amount, auto_cashout_target, status, balance
    """
    try:
        # Parse request
        import json
        data = json.loads(request.body)
        
        # Get amount
        try:
            amount = Decimal(str(data.get('amount', 0)))
        except (InvalidOperation, ValueError):
            return JsonResponse({
                'error': 'Неверная сумма ставки'
            }, status=400)
        
        # Get auto cashout target (optional)
        auto_cashout_target = None
        if 'auto_cashout_target' in data and data['auto_cashout_target']:
            try:
                auto_cashout_target = Decimal(str(data['auto_cashout_target']))
            except (InvalidOperation, ValueError):
                return JsonResponse({
                    'error': 'Неверная цель авто-кэшаута'
                }, status=400)
        
        # Place bet
        bet = CrashGameService.place_bet(
            user=request.user,
            amount=amount,
            auto_cashout_target=auto_cashout_target
        )
        
        # Get updated balance
        request.user.profile.refresh_from_db()
        balance = request.user.profile.balance
        
        return JsonResponse({
            'bet_id': bet.id,
            'round_id': str(bet.round.round_id),
            'bet_amount': str(bet.bet_amount),
            'auto_cashout_target': str(bet.auto_cashout_target) if bet.auto_cashout_target else None,
            'status': bet.status,
            'balance': str(balance)
        })
    
    except ValidationError as e:
        return JsonResponse({
            'error': str(e.message) if hasattr(e, 'message') else str(e)
        }, status=400)
    
    except InsufficientFundsError as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def cashout(request):
    """
    POST /api/games/crash/cashout/
    
    Cash out an active bet.
    
    Request body:
        - bet_id: Bet ID to cash out (required)
    
    Returns:
        - bet_id, cashout_multiplier, win_amount, status, balance
    """
    try:
        # Parse request
        import json
        data = json.loads(request.body)
        
        # Get bet_id
        bet_id = data.get('bet_id')
        if not bet_id:
            return JsonResponse({
                'error': 'Не указан bet_id'
            }, status=400)
        
        # Cash out
        bet = CrashGameService.cashout(
            user=request.user,
            bet_id=int(bet_id)
        )
        
        # Get updated balance
        request.user.profile.refresh_from_db()
        balance = request.user.profile.balance
        
        return JsonResponse({
            'bet_id': bet.id,
            'cashout_multiplier': str(bet.cashout_multiplier),
            'win_amount': str(bet.win_amount),
            'status': bet.status,
            'balance': str(balance)
        })
    
    except ValidationError as e:
        return JsonResponse({
            'error': str(e.message) if hasattr(e, 'message') else str(e)
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def round_history(request):
    """
    GET /api/games/crash/history/
    
    Get history of recent rounds.
    
    Returns:
        - rounds: List of rounds with round_id, crash_point, crashed_at
    """
    try:
        rounds = CrashGameService.get_round_history(limit=50)
        
        rounds_data = []
        for round_instance in rounds:
            rounds_data.append({
                'round_id': str(round_instance.round_id),
                'crash_point': str(round_instance.crash_point),
                'crashed_at': round_instance.crashed_at.isoformat() if round_instance.crashed_at else None
            })
        
        return JsonResponse({
            'rounds': rounds_data
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
