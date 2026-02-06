# Authentication API Examples

## Base URL
```
http://localhost:8000/api/auth/
```

## 1. User Registration

### Endpoint
```
POST /api/auth/register/
```

### Request
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Success Response (201 Created)
```json
{
  "success": true,
  "message": "Пользователь успешно зарегистрирован",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "balance": 1000.0
  }
}
```

### Error Response (400 Bad Request)
```json
{
  "success": false,
  "errors": [
    "Пользователь с именем 'john_doe' уже существует"
  ]
}
```

### Validation Errors
```json
{
  "success": false,
  "errors": [
    "Имя пользователя должно содержать минимум 3 символа",
    "Неверный формат email адреса",
    "Пароль должен содержать минимум 8 символов"
  ]
}
```

---

## 2. User Login

### Endpoint
```
POST /api/auth/login/
```

### Request (with username)
```json
{
  "username": "john_doe",
  "password": "SecurePass123"
}
```

### Request (with email)
```json
{
  "username": "john@example.com",
  "password": "SecurePass123"
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Вход выполнен успешно",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "balance": 1000.0
  }
}
```

### Error Response (401 Unauthorized)
```json
{
  "success": false,
  "error": "Неверное имя пользователя или пароль"
}
```

---

## 3. User Logout

### Endpoint
```
POST /api/auth/logout/
```

### Request
No body required. Must be authenticated.

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Выход выполнен успешно"
}
```

### Error Response (401 Unauthorized)
Redirects to login page if not authenticated.

---

## 4. Get Current User

### Endpoint
```
GET /api/auth/me/
```

### Request
No body required. Must be authenticated.

### Success Response (200 OK)
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2026-02-05T21:34:14.554665+00:00",
    "balance": 1000.0,
    "total_wagered": 0.0,
    "total_won": 0.0
  }
}
```

### Error Response (401 Unauthorized)
Redirects to login page if not authenticated.

---

## 5. Get User Profile

### Endpoint
```
GET /api/auth/profile/
```

### Request
No body required. Must be authenticated.

### Success Response (200 OK)
```json
{
  "success": true,
  "profile": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "date_joined": "2026-02-05T21:34:14.554665+00:00"
    },
    "balance": 1000.0,
    "total_wagered": 0.0,
    "total_won": 0.0,
    "profile_created_at": "2026-02-05T21:34:17.318284+00:00",
    "profile_updated_at": "2026-02-05T21:34:25.858440+00:00"
  }
}
```

### Error Response (401 Unauthorized)
Redirects to login page if not authenticated.

---

## Complete Flow Example

### 1. Register
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "password": "TestPass123"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "TestPass123"
  }' \
  -c cookies.txt
```

### 3. Get Current User
```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -b cookies.txt
```

### 4. Get Profile
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -b cookies.txt
```

### 5. Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -b cookies.txt
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created (registration successful) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (authentication required or failed) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found (resource doesn't exist) |
| 500 | Internal Server Error |

---

## Common Validation Errors

### Username
- "Имя пользователя обязательно для заполнения"
- "Имя пользователя должно содержать минимум 3 символа"
- "Имя пользователя слишком длинное (максимум 150 символов)"
- "Имя пользователя может содержать только буквы, цифры, дефис и подчеркивание"
- "Пользователь с именем 'xxx' уже существует"

### Email
- "Email обязателен для заполнения"
- "Неверный формат email адреса"
- "Email слишком длинный (максимум 254 символа)"
- "Email 'xxx' уже зарегистрирован"

### Password
- "Пароль обязателен для заполнения"
- "Пароль должен содержать минимум 8 символов"
- "Пароль слишком длинный (максимум 128 символов)"
- "Пароль должен содержать хотя бы одну цифру"
- "Пароль должен содержать хотя бы одну букву"

---

## Authentication

The API uses session-based authentication. After successful login, a session cookie is set and must be included in subsequent requests.

### Session Cookie
- Name: `sessionid`
- HttpOnly: `true`
- Secure: `false` (development), `true` (production)
- SameSite: `Lax`
- Max-Age: `3600` seconds (1 hour)

### CSRF Protection
CSRF protection is currently disabled for API endpoints (`@csrf_exempt`). In production, implement proper CSRF token handling.

---

## Testing with Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/auth"

# Create session
session = requests.Session()

# Register
response = session.post(f"{BASE_URL}/register/", json={
    "username": "test_user",
    "email": "test@example.com",
    "password": "TestPass123"
})
print(response.json())

# Login
response = session.post(f"{BASE_URL}/login/", json={
    "username": "test_user",
    "password": "TestPass123"
})
print(response.json())

# Get current user
response = session.get(f"{BASE_URL}/me/")
print(response.json())

# Get profile
response = session.get(f"{BASE_URL}/profile/")
print(response.json())

# Logout
response = session.post(f"{BASE_URL}/logout/")
print(response.json())
```

---

## Testing with JavaScript (Fetch API)

```javascript
const BASE_URL = 'http://localhost:8000/api/auth';

// Register
fetch(`${BASE_URL}/register/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'test_user',
    email: 'test@example.com',
    password: 'TestPass123'
  }),
  credentials: 'include'  // Include cookies
})
.then(response => response.json())
.then(data => console.log(data));

// Login
fetch(`${BASE_URL}/login/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'test_user',
    password: 'TestPass123'
  }),
  credentials: 'include'
})
.then(response => response.json())
.then(data => console.log(data));

// Get current user
fetch(`${BASE_URL}/me/`, {
  credentials: 'include'
})
.then(response => response.json())
.then(data => console.log(data));

// Logout
fetch(`${BASE_URL}/logout/`, {
  method: 'POST',
  credentials: 'include'
})
.then(response => response.json())
.then(data => console.log(data));
```
