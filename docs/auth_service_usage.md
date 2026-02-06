# AuthService Usage Examples

## Overview

`AuthService` - это сервис для управления аутентификацией пользователей в системе онлайн-казино. Следует принципу Single Responsibility и содержит только логику аутентификации.

## Import

```python
from users.services import AuthService
from django.core.exceptions import ValidationError
```

## 1. User Registration

### Basic Registration

```python
try:
    user = AuthService.register_user(
        username='john_doe',
        email='john@example.com',
        password='SecurePass123'
    )
    print(f"User registered: {user.username}")
    print(f"Initial balance: {user.profile.balance}")
except ValidationError as e:
    print(f"Registration failed: {e}")
```

### Registration with Full Name

```python
user = AuthService.register_user(
    username='jane_smith',
    email='jane@example.com',
    password='MyPass456',
    first_name='Jane',
    last_name='Smith'
)
print(f"Welcome, {user.get_full_name()}!")
```

### Handling Registration Errors

```python
try:
    user = AuthService.register_user(
        username='test',
        email='invalid-email',
        password='weak'
    )
except ValidationError as e:
    # e.messages will contain list of errors:
    # - "Имя пользователя должно содержать минимум 3 символа"
    # - "Неверный формат email адреса"
    # - "Пароль должен содержать минимум 8 символов"
    for error in e.messages:
        print(f"Error: {error}")
```

## 2. User Authentication

### Authenticate with Username

```python
user = AuthService.authenticate_user('john_doe', 'SecurePass123')
if user:
    print(f"Welcome back, {user.username}!")
else:
    print("Invalid credentials")
```

### Authenticate with Email

```python
# AuthService automatically detects if username is actually an email
user = AuthService.authenticate_user('john@example.com', 'SecurePass123')
if user:
    print(f"Authenticated: {user.username}")
```

### Login User (Create Session)

```python
from django.http import HttpRequest

def login_view(request):
    user = AuthService.authenticate_user(
        request.POST['username'],
        request.POST['password']
    )
    
    if user:
        AuthService.login_user(request, user)
        return redirect('profile')
    else:
        return render(request, 'login.html', {
            'error': 'Неверное имя пользователя или пароль'
        })
```

## 3. User Logout

```python
def logout_view(request):
    AuthService.logout_user(request)
    return redirect('login')
```

## 4. Profile Retrieval

### Get User Profile Data

```python
user = request.user
profile_data = AuthService.get_user_profile(user)

# profile_data contains:
# {
#     'id': 1,
#     'username': 'john_doe',
#     'email': 'john@example.com',
#     'first_name': 'John',
#     'last_name': 'Doe',
#     'date_joined': datetime(...),
#     'balance': 1000.0,
#     'total_wagered': 0.0,
#     'total_won': 0.0,
#     'profile_created_at': datetime(...),
#     'profile_updated_at': datetime(...)
# }

print(f"Balance: {profile_data['balance']} ₽")
```

## 5. User Lookup

### Get User by ID

```python
user = AuthService.get_user_by_id(1)
if user:
    print(f"Found: {user.username}")
else:
    print("User not found")
```

### Get User by Username

```python
user = AuthService.get_user_by_username('john_doe')
if user:
    print(f"Email: {user.email}")
```

### Get User by Email

```python
user = AuthService.get_user_by_email('john@example.com')
if user:
    print(f"Username: {user.username}")
```

## 6. Validation Methods

### Check if Username Exists

```python
if AuthService.check_username_exists('john_doe'):
    print("Username already taken")
else:
    print("Username available")
```

### Check if Email Exists

```python
if AuthService.check_email_exists('john@example.com'):
    print("Email already registered")
else:
    print("Email available")
```

### Validate Input Data

```python
# Validate email
try:
    AuthService.validate_email('test@example.com')
    print("Email is valid")
except ValidationError as e:
    print(f"Invalid email: {e}")

# Validate username
try:
    AuthService.validate_username('john_doe')
    print("Username is valid")
except ValidationError as e:
    print(f"Invalid username: {e}")

# Validate password
try:
    AuthService.validate_password('SecurePass123')
    print("Password is valid")
except ValidationError as e:
    print(f"Invalid password: {e}")
```

## 7. Complete Registration Flow Example

```python
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Check password confirmation
        if password != password_confirm:
            return render(request, 'register.html', {
                'error': 'Пароли не совпадают'
            })
        
        try:
            # Register user
            user = AuthService.register_user(
                username=username,
                email=email,
                password=password
            )
            
            # Auto-login after registration
            AuthService.login_user(request, user)
            
            # Redirect to profile
            return redirect('profile')
            
        except ValidationError as e:
            return render(request, 'register.html', {
                'errors': e.messages,
                'username': username,
                'email': email
            })
    
    return render(request, 'register.html')
```

## 8. Complete Login Flow Example

```python
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = AuthService.authenticate_user(username, password)
        
        if user:
            # Login user
            AuthService.login_user(request, user)
            
            # Get profile data
            profile_data = AuthService.get_user_profile(user)
            
            # Log successful login
            logger.info(f"User {user.username} logged in with balance {profile_data['balance']}")
            
            # Redirect to dashboard
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {
                'error': 'Неверное имя пользователя или пароль',
                'username': username
            })
    
    return render(request, 'login.html')
```

## 9. Error Handling Best Practices

```python
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def safe_register_user(username, email, password):
    """
    Safely register user with comprehensive error handling
    """
    try:
        user = AuthService.register_user(username, email, password)
        logger.info(f"User registered successfully: {username}")
        return {'success': True, 'user': user}
        
    except ValidationError as e:
        logger.warning(f"Registration validation failed: {e.messages}")
        return {'success': False, 'errors': e.messages}
        
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        return {'success': False, 'errors': ['Произошла ошибка. Попробуйте позже.']}
```

## 10. Testing AuthService

```python
import pytest
from users.services import AuthService
from django.core.exceptions import ValidationError

def test_user_registration():
    """Test successful user registration"""
    user = AuthService.register_user(
        username='test_user',
        email='test@example.com',
        password='TestPass123'
    )
    
    assert user.username == 'test_user'
    assert user.email == 'test@example.com'
    assert hasattr(user, 'profile')
    assert user.profile.balance == 1000.00

def test_duplicate_username():
    """Test registration with duplicate username"""
    AuthService.register_user('duplicate', 'test1@example.com', 'Pass123')
    
    with pytest.raises(ValidationError):
        AuthService.register_user('duplicate', 'test2@example.com', 'Pass123')

def test_authentication():
    """Test user authentication"""
    user = AuthService.register_user('auth_test', 'auth@example.com', 'Pass123')
    
    # Test successful auth
    auth_user = AuthService.authenticate_user('auth_test', 'Pass123')
    assert auth_user is not None
    assert auth_user.username == 'auth_test'
    
    # Test failed auth
    auth_user = AuthService.authenticate_user('auth_test', 'WrongPass')
    assert auth_user is None
```

## Validation Rules

### Username
- Минимум 3 символа
- Максимум 150 символов
- Только буквы, цифры, дефис и подчеркивание
- Должен быть уникальным

### Email
- Валидный email формат
- Максимум 254 символа
- Должен быть уникальным

### Password
- Минимум 8 символов
- Максимум 128 символов
- Должен содержать хотя бы одну цифру
- Должен содержать хотя бы одну букву

## Logging

AuthService логирует следующие события:

- `INFO`: Успешная регистрация, успешная аутентификация, выход
- `WARNING`: Неудачная аутентификация, попытка доступа к несуществующему пользователю
- `ERROR`: Ошибки базы данных, неожиданные ошибки

Пример логов:
```
INFO users Attempting to register user: john_doe
INFO users User registered successfully: john_doe (ID: 1)
INFO users Profile created with balance: 1000.00
INFO users Authentication attempt for: john_doe
INFO users Authentication successful for: john_doe
INFO users User logged out: john_doe
```
