"""
Wallet API views.
All views use WalletService for business logic (SRP).
"""
import logging
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from users.models import User
from .services import WalletService, InsufficientFundsError

logger = logging.getLogger('wallet')


@login_required
@require_http_methods(["GET"])
def get_balance(request):
    """
    Get current user balance.
    
    GET /api/wallet/balance/
    
    Response:
        200: {"balance": "1500.00", "currency": "RUB"}
        401: {"error": "Требуется авторизация"}
    """
    try:
        balance = WalletService.get_balance(request.user)
        
        logger.info(f"Balance retrieved for {request.user.username}: {balance}")
        
        return JsonResponse({
            'balance': str(balance),
            'currency': 'RUB'
        }, status=200)
        
    except ValidationError as e:
        logger.error(f"Balance retrieval failed for {request.user.username}: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error in get_balance: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def demo_deposit(request):
    """
    Add demo funds to user balance (fixed 500 RUB).
    
    POST /api/wallet/deposit/
    
    Response:
        200: {
            "success": true,
            "amount": "500.00",
            "balance": "2000.00",
            "transaction_id": 123
        }
        400: {"error": "Ошибка валидации"}
        401: {"error": "Требуется авторизация"}
    """
    try:
        # Create deposit transaction
        txn = WalletService.deposit(request.user)
        
        logger.info(
            f"Demo deposit completed for {request.user.username}: "
            f"{txn.amount} (balance: {txn.balance_after})"
        )
        
        return JsonResponse({
            'success': True,
            'amount': str(txn.amount),
            'new_balance': str(txn.balance_after),
            'balance': str(txn.balance_after),
            'transaction_id': txn.id,
            'description': txn.description
        }, status=200)
        
    except ValidationError as e:
        logger.error(f"Demo deposit failed for {request.user.username}: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error in demo_deposit: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_transactions(request):
    """
    Get user transaction history.
    
    GET /api/wallet/transactions/?limit=50&type=deposit&status=completed
    
    Query Parameters:
        - limit: Maximum number of transactions (default: 50)
        - type: Filter by transaction type (deposit/bet/win/bonus)
        - status: Filter by status (pending/completed/failed)
    
    Response:
        200: {
            "transactions": [
                {
                    "id": 123,
                    "amount": "500.00",
                    "type": "deposit",
                    "type_display": "Депозит",
                    "balance_before": "1000.00",
                    "balance_after": "1500.00",
                    "description": "Демо-пополнение 500.00 ₽",
                    "status": "completed",
                    "status_display": "Завершена",
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ],
            "count": 10
        }
        401: {"error": "Требуется авторизация"}
    """
    try:
        # Get query parameters
        limit = int(request.GET.get('limit', 50))
        transaction_type = request.GET.get('type', None)
        status = request.GET.get('status', None)
        
        # Validate limit
        if limit < 1 or limit > 100:
            return JsonResponse({
                'error': 'Лимит должен быть от 1 до 100'
            }, status=400)
        
        # Get transactions
        transactions = WalletService.get_transaction_history(
            request.user,
            limit=limit,
            transaction_type=transaction_type,
            status=status
        )
        
        # Format response
        transactions_data = [
            {
                'id': txn.id,
                'amount': str(txn.amount),
                'type': txn.transaction_type,
                'type_display': txn.get_transaction_type_display(),
                'balance_before': str(txn.balance_before),
                'balance_after': str(txn.balance_after),
                'description': txn.description,
                'status': txn.status,
                'status_display': txn.get_status_display(),
                'created_at': txn.created_at.isoformat()
            }
            for txn in transactions
        ]
        
        logger.info(
            f"Transactions retrieved for {request.user.username}: "
            f"{len(transactions_data)} items"
        )
        
        return JsonResponse({
            'transactions': transactions_data,
            'count': len(transactions_data)
        }, status=200)
        
    except ValueError as e:
        logger.error(f"Invalid query parameter: {e}")
        return JsonResponse({
            'error': 'Неверный формат параметров'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error in get_transactions: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_balance_summary(request):
    """
    Get balance summary with statistics.
    
    GET /api/wallet/summary/
    
    Response:
        200: {
            "balance": 2450.0,
            "total_wagered": 100.0,
            "total_won": 250.0,
            "total_deposits": 1250.0,
            "total_bonuses": 50.0,
            "net_profit": 150.0,
            "transaction_count": 6
        }
        401: {"error": "Требуется авторизация"}
    """
    try:
        summary = WalletService.get_balance_summary(request.user)
        
        logger.info(f"Balance summary retrieved for {request.user.username}")
        
        return JsonResponse(summary, status=200)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_balance_summary: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера'
        }, status=500)
