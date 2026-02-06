"""
Views for user authentication and profile management.
All views return JSON responses for API consumption.
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .services import AuthService

logger = logging.getLogger('users')


def json_response(data, status=200):
    """Helper function to create JSON response"""
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def parse_json_body(request):
    """Parse JSON body from request"""
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


@require_http_methods(["POST"])
@csrf_exempt  # For API, we'll handle CSRF differently in production
def register_view(request):
    """
    User registration endpoint.
    
    POST /api/auth/register/
    
    Request body:
    {
        "username": "string",
        "email": "string",
        "password": "string",
        "first_name": "string" (optional),
        "last_name": "string" (optional)
    }
    
    Response 201:
    {
        "success": true,
        "message": "Пользователь успешно зарегистрирован",
        "user": {
            "id": int,
            "username": "string",
            "email": "string",
            "first_name": "string",
            "last_name": "string"
        }
    }
    
    Response 400:
    {
        "success": false,
        "errors": ["error message 1", "error message 2"]
    }
    """
    logger.info(f"Registration request from {request.META.get('REMOTE_ADDR')}")
    
    # Parse request body
    data = parse_json_body(request)
    if data is None:
        logger.warning("Invalid JSON in registration request")
        return json_response({
            'success': False,
            'errors': ['Неверный формат данных']
        }, status=400)
    
    # Extract fields
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    # Validate required fields
    if not username or not email or not password:
        logger.warning("Missing required fields in registration")
        return json_response({
            'success': False,
            'errors': ['Все обязательные поля должны быть заполнены']
        }, status=400)
    
    try:
        # Register user via AuthService
        user = AuthService.register_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        logger.info(f"User registered successfully: {username}")
        
        return json_response({
            'success': True,
            'message': 'Пользователь успешно зарегистрирован',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'balance': float(user.profile.balance)
            }
        }, status=201)
        
    except ValidationError as e:
        logger.warning(f"Registration validation failed: {e.messages}")
        return json_response({
            'success': False,
            'errors': e.messages
        }, status=400)
        
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        return json_response({
            'success': False,
            'errors': ['Произошла ошибка при регистрации. Попробуйте позже.']
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def login_view(request):
    """
    User login endpoint.
    
    POST /api/auth/login/
    
    Request body:
    {
        "username": "string",  # Can be username or email
        "password": "string"
    }
    
    Response 200:
    {
        "success": true,
        "message": "Вход выполнен успешно",
        "user": {
            "id": int,
            "username": "string",
            "email": "string",
            "balance": float
        }
    }
    
    Response 401:
    {
        "success": false,
        "error": "Неверное имя пользователя или пароль"
    }
    """
    logger.info(f"Login request from {request.META.get('REMOTE_ADDR')}")
    
    # Parse request body
    data = parse_json_body(request)
    if data is None:
        logger.warning("Invalid JSON in login request")
        return json_response({
            'success': False,
            'error': 'Неверный формат данных'
        }, status=400)
    
    # Extract credentials
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # Validate required fields
    if not username or not password:
        logger.warning("Missing credentials in login request")
        return json_response({
            'success': False,
            'error': 'Имя пользователя и пароль обязательны'
        }, status=400)
    
    # Authenticate user
    user = AuthService.authenticate_user(username, password)
    
    if user is None:
        logger.warning(f"Failed login attempt for: {username}")
        return json_response({
            'success': False,
            'error': 'Неверное имя пользователя или пароль'
        }, status=401)
    
    # Login user (create session)
    AuthService.login_user(request, user)
    
    logger.info(f"User logged in successfully: {user.username}")
    
    return json_response({
        'success': True,
        'message': 'Вход выполнен успешно',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'balance': float(user.profile.balance)
        }
    }, status=200)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def logout_view(request):
    """
    User logout endpoint.
    
    POST /api/auth/logout/
    
    Response 200:
    {
        "success": true,
        "message": "Выход выполнен успешно"
    }
    """
    username = request.user.username
    logger.info(f"Logout request from: {username}")
    
    # Logout user
    AuthService.logout_user(request)
    
    logger.info(f"User logged out successfully: {username}")
    
    return json_response({
        'success': True,
        'message': 'Выход выполнен успешно'
    }, status=200)


@require_http_methods(["GET"])
@login_required
def current_user_view(request):
    """
    Get current authenticated user data.
    
    GET /api/auth/me/
    
    Response 200:
    {
        "success": true,
        "user": {
            "id": int,
            "username": "string",
            "email": "string",
            "first_name": "string",
            "last_name": "string",
            "date_joined": "datetime",
            "balance": float,
            "total_wagered": float,
            "total_won": float
        }
    }
    
    Response 401:
    {
        "success": false,
        "error": "Требуется аутентификация"
    }
    """
    logger.info(f"Current user request from: {request.user.username}")
    
    try:
        # Get user profile data
        profile_data = AuthService.get_user_profile(request.user)
        
        return json_response({
            'success': True,
            'user': {
                'id': profile_data['id'],
                'username': profile_data['username'],
                'email': profile_data['email'],
                'first_name': profile_data['first_name'],
                'last_name': profile_data['last_name'],
                'date_joined': profile_data['date_joined'].isoformat(),
                'balance': profile_data['balance'],
                'total_wagered': profile_data['total_wagered'],
                'total_won': profile_data['total_won']
            }
        }, status=200)
        
    except ValidationError as e:
        logger.error(f"Profile not found for user: {request.user.username}")
        return json_response({
            'success': False,
            'error': str(e)
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error retrieving current user: {e}")
        return json_response({
            'success': False,
            'error': 'Ошибка при получении данных пользователя'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def profile_view(request):
    """
    Get user profile with detailed information.
    
    GET /api/auth/profile/
    
    Response 200:
    {
        "success": true,
        "profile": {
            "user": {
                "id": int,
                "username": "string",
                "email": "string",
                "first_name": "string",
                "last_name": "string",
                "date_joined": "datetime"
            },
            "balance": float,
            "total_wagered": float,
            "total_won": float,
            "profile_created_at": "datetime",
            "profile_updated_at": "datetime"
        }
    }
    """
    logger.info(f"Profile request from: {request.user.username}")
    
    try:
        # Get user profile data
        profile_data = AuthService.get_user_profile(request.user)
        
        return json_response({
            'success': True,
            'profile': {
                'user': {
                    'id': profile_data['id'],
                    'username': profile_data['username'],
                    'email': profile_data['email'],
                    'first_name': profile_data['first_name'],
                    'last_name': profile_data['last_name'],
                    'date_joined': profile_data['date_joined'].isoformat()
                },
                'balance': profile_data['balance'],
                'total_wagered': profile_data['total_wagered'],
                'total_won': profile_data['total_won'],
                'profile_created_at': profile_data['profile_created_at'].isoformat(),
                'profile_updated_at': profile_data['profile_updated_at'].isoformat()
            }
        }, status=200)
        
    except ValidationError as e:
        logger.error(f"Profile not found for user: {request.user.username}")
        return json_response({
            'success': False,
            'error': str(e)
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        return json_response({
            'success': False,
            'error': 'Ошибка при получении профиля'
        }, status=500)

