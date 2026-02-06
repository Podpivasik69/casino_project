"""
Authentication service for user management.
Handles user registration, authentication, and profile operations.
"""
import logging
import re
from typing import Optional, Dict, Any
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from .models import User, Profile

logger = logging.getLogger('users')


class AuthService:
    """
    Service for user authentication operations.
    Follows Single Responsibility Principle - handles only auth logic.
    """
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,150}$')
    
    @staticmethod
    def validate_email(email: str) -> None:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Raises:
            ValidationError: If email format is invalid
        """
        if not email:
            raise ValidationError("Email обязателен для заполнения")
        
        if not AuthService.EMAIL_PATTERN.match(email):
            raise ValidationError("Неверный формат email адреса")
        
        if len(email) > 254:
            raise ValidationError("Email слишком длинный (максимум 254 символа)")
    
    @staticmethod
    def validate_username(username: str) -> None:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            
        Raises:
            ValidationError: If username format is invalid
        """
        if not username:
            raise ValidationError("Имя пользователя обязательно для заполнения")
        
        if len(username) < 3:
            raise ValidationError("Имя пользователя должно содержать минимум 3 символа")
        
        if len(username) > 150:
            raise ValidationError("Имя пользователя слишком длинное (максимум 150 символов)")
        
        if not AuthService.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Имя пользователя может содержать только буквы, цифры, дефис и подчеркивание"
            )
    
    @staticmethod
    def validate_password(password: str) -> None:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Raises:
            ValidationError: If password is too weak
        """
        if not password:
            raise ValidationError("Пароль обязателен для заполнения")
        
        if len(password) < 8:
            raise ValidationError("Пароль должен содержать минимум 8 символов")
        
        if len(password) > 128:
            raise ValidationError("Пароль слишком длинный (максимум 128 символов)")
        
        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру")
        
        # Check for at least one letter
        if not any(char.isalpha() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну букву")
    
    @staticmethod
    def check_username_exists(username: str) -> bool:
        """
        Check if username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if username exists, False otherwise
        """
        return User.objects.filter(username=username).exists()
    
    @staticmethod
    def check_email_exists(email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists, False otherwise
        """
        return User.objects.filter(email=email).exists()
    
    @staticmethod
    @transaction.atomic
    def register_user(username: str, email: str, password: str, 
                     first_name: str = '', last_name: str = '') -> User:
        """
        Register new user with profile.
        
        Steps:
        1. Validate input data
        2. Check username/email uniqueness
        3. Create User with hashed password
        4. Profile is created automatically via signal
        5. Return User instance
        
        Args:
            username: Unique username
            email: Unique email address
            password: User password (will be hashed)
            first_name: Optional first name
            last_name: Optional last name
            
        Returns:
            Created User instance with profile
            
        Raises:
            ValidationError: Invalid input data or duplicate username/email
        """
        logger.info(f"Attempting to register user: {username}")
        
        try:
            # Validate input data
            AuthService.validate_username(username)
            AuthService.validate_email(email)
            AuthService.validate_password(password)
            
            # Check uniqueness
            if AuthService.check_username_exists(username):
                raise ValidationError(f"Пользователь с именем '{username}' уже существует")
            
            if AuthService.check_email_exists(email):
                raise ValidationError(f"Email '{email}' уже зарегистрирован")
            
            # Create user (password will be hashed automatically)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Verify profile was created
            if not hasattr(user, 'profile'):
                logger.error(f"Profile was not created for user {username}")
                raise ValidationError("Ошибка создания профиля пользователя")
            
            logger.info(f"User registered successfully: {username} (ID: {user.id})")
            logger.info(f"Profile created with balance: {user.profile.balance}")
            
            return user
            
        except IntegrityError as e:
            logger.error(f"Database integrity error during registration: {e}")
            raise ValidationError("Ошибка при создании пользователя. Попробуйте другое имя или email.")
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}")
            raise
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username or email
            password: User password
            
        Returns:
            User instance if valid, None otherwise
        """
        logger.info(f"Authentication attempt for: {username}")
        
        if not username or not password:
            logger.warning("Authentication failed: empty username or password")
            return None
        
        # Try to authenticate with username
        user = authenticate(username=username, password=password)
        
        # If failed, try with email
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            if user.is_active:
                logger.info(f"Authentication successful for: {username}")
                return user
            else:
                logger.warning(f"Authentication failed: user {username} is inactive")
                return None
        else:
            logger.warning(f"Authentication failed: invalid credentials for {username}")
            return None
    
    @staticmethod
    def login_user(request, user: User) -> None:
        """
        Login user and create session.
        
        Args:
            request: Django request object
            user: User instance to login
        """
        login(request, user)
        logger.info(f"User logged in: {user.username}")
    
    @staticmethod
    def logout_user(request) -> None:
        """
        Logout user and clear session.
        
        Args:
            request: Django request object
        """
        username = request.user.username if request.user.is_authenticated else 'Anonymous'
        logout(request)
        logger.info(f"User logged out: {username}")
    
    @staticmethod
    def get_user_profile(user: User) -> Dict[str, Any]:
        """
        Get user profile data.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with user and profile data
            
        Raises:
            ValidationError: If profile doesn't exist
        """
        if not hasattr(user, 'profile'):
            logger.error(f"Profile not found for user: {user.username}")
            raise ValidationError("Профиль пользователя не найден")
        
        profile = user.profile
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined,
            'balance': float(profile.balance),
            'total_wagered': float(profile.total_wagered),
            'total_won': float(profile.total_won),
            'profile_created_at': profile.created_at,
            'profile_updated_at': profile.updated_at,
        }
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance or None
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"User not found: ID {user_id}")
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User instance or None
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(f"User not found: {username}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: Email address
            
        Returns:
            User instance or None
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"User not found: {email}")
            return None
