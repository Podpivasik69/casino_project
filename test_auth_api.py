"""
Test script for Authentication API endpoints.
Tests all views using Django test client.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

import json
from django.test import Client
from users.models import User


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_request(method, url, data=None):
    """Print request details"""
    print(f"\n📤 {method} {url}")
    if data:
        print(f"   Body: {json.dumps(data, indent=2, ensure_ascii=False)}")


def print_response(response):
    """Print response details"""
    print(f"\n📥 Status: {response.status_code}")
    try:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"   Response: {response.content}")


def test_registration():
    """Test user registration endpoint"""
    print_section("1. Testing Registration API")
    
    client = Client()
    
    # Clean up test user
    User.objects.filter(username='api_test_user').delete()
    
    # Test 1: Successful registration
    print("\n✅ Test 1: Successful Registration")
    data = {
        'username': 'api_test_user',
        'email': 'api_test@example.com',
        'password': 'TestPass123',
        'first_name': 'API',
        'last_name': 'Test'
    }
    print_request('POST', '/api/auth/register/', data)
    
    response = client.post(
        '/api/auth/register/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    assert response.json()['success'] == True
    print("   ✓ Registration successful")
    
    # Test 2: Duplicate username
    print("\n❌ Test 2: Duplicate Username")
    data = {
        'username': 'api_test_user',  # Same username
        'email': 'different@example.com',
        'password': 'TestPass123'
    }
    print_request('POST', '/api/auth/register/', data)
    
    response = client.post(
        '/api/auth/register/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert response.json()['success'] == False
    print("   ✓ Duplicate username correctly rejected")
    
    # Test 3: Invalid email
    print("\n❌ Test 3: Invalid Email")
    data = {
        'username': 'api_test_user2',
        'email': 'invalid-email',
        'password': 'TestPass123'
    }
    print_request('POST', '/api/auth/register/', data)
    
    response = client.post(
        '/api/auth/register/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 400
    print("   ✓ Invalid email correctly rejected")
    
    # Test 4: Weak password
    print("\n❌ Test 4: Weak Password")
    data = {
        'username': 'api_test_user3',
        'email': 'test3@example.com',
        'password': 'weak'
    }
    print_request('POST', '/api/auth/register/', data)
    
    response = client.post(
        '/api/auth/register/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 400
    print("   ✓ Weak password correctly rejected")
    
    # Test 5: Missing fields
    print("\n❌ Test 5: Missing Required Fields")
    data = {
        'username': 'api_test_user4'
        # Missing email and password
    }
    print_request('POST', '/api/auth/register/', data)
    
    response = client.post(
        '/api/auth/register/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 400
    print("   ✓ Missing fields correctly rejected")


def test_login():
    """Test user login endpoint"""
    print_section("2. Testing Login API")
    
    client = Client()
    
    # Test 1: Successful login with username
    print("\n✅ Test 1: Login with Username")
    data = {
        'username': 'api_test_user',
        'password': 'TestPass123'
    }
    print_request('POST', '/api/auth/login/', data)
    
    response = client.post(
        '/api/auth/login/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 200
    assert response.json()['success'] == True
    print("   ✓ Login successful")
    
    # Save session for authenticated requests
    session_cookie = response.cookies.get('sessionid')
    
    # Test 2: Login with email
    print("\n✅ Test 2: Login with Email")
    data = {
        'username': 'api_test@example.com',  # Using email
        'password': 'TestPass123'
    }
    print_request('POST', '/api/auth/login/', data)
    
    response = client.post(
        '/api/auth/login/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 200
    assert response.json()['success'] == True
    print("   ✓ Login with email successful")
    
    # Test 3: Wrong password
    print("\n❌ Test 3: Wrong Password")
    data = {
        'username': 'api_test_user',
        'password': 'WrongPass123'
    }
    print_request('POST', '/api/auth/login/', data)
    
    response = client.post(
        '/api/auth/login/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 401
    assert response.json()['success'] == False
    print("   ✓ Wrong password correctly rejected")
    
    # Test 4: Non-existent user
    print("\n❌ Test 4: Non-existent User")
    data = {
        'username': 'nonexistent_user',
        'password': 'SomePass123'
    }
    print_request('POST', '/api/auth/login/', data)
    
    response = client.post(
        '/api/auth/login/',
        data=json.dumps(data),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 401
    print("   ✓ Non-existent user correctly rejected")
    
    return client  # Return client with session


def test_current_user(client):
    """Test current user endpoint"""
    print_section("3. Testing Current User API")
    
    # Test 1: Get current user (authenticated)
    print("\n✅ Test 1: Get Current User (Authenticated)")
    print_request('GET', '/api/auth/me/')
    
    response = client.get('/api/auth/me/')
    print_response(response)
    
    assert response.status_code == 200
    assert response.json()['success'] == True
    assert 'user' in response.json()
    print("   ✓ Current user data retrieved")
    
    # Test 2: Get current user (not authenticated)
    print("\n❌ Test 2: Get Current User (Not Authenticated)")
    new_client = Client()  # New client without session
    print_request('GET', '/api/auth/me/')
    
    response = new_client.get('/api/auth/me/')
    print_response(response)
    
    # Django redirects to login page for @login_required
    assert response.status_code in [302, 401]
    print("   ✓ Unauthenticated request correctly rejected")


def test_profile(client):
    """Test profile endpoint"""
    print_section("4. Testing Profile API")
    
    # Test 1: Get profile (authenticated)
    print("\n✅ Test 1: Get Profile (Authenticated)")
    print_request('GET', '/api/auth/profile/')
    
    response = client.get('/api/auth/profile/')
    print_response(response)
    
    assert response.status_code == 200
    assert response.json()['success'] == True
    assert 'profile' in response.json()
    
    profile = response.json()['profile']
    assert 'user' in profile
    assert 'balance' in profile
    assert 'total_wagered' in profile
    assert 'total_won' in profile
    print("   ✓ Profile data retrieved")
    print(f"   - Balance: {profile['balance']}")
    print(f"   - Total Wagered: {profile['total_wagered']}")
    print(f"   - Total Won: {profile['total_won']}")
    
    # Test 2: Get profile (not authenticated)
    print("\n❌ Test 2: Get Profile (Not Authenticated)")
    new_client = Client()
    print_request('GET', '/api/auth/profile/')
    
    response = new_client.get('/api/auth/profile/')
    print_response(response)
    
    assert response.status_code in [302, 401]
    print("   ✓ Unauthenticated request correctly rejected")


def test_logout(client):
    """Test logout endpoint"""
    print_section("5. Testing Logout API")
    
    # Test 1: Logout (authenticated)
    print("\n✅ Test 1: Logout (Authenticated)")
    print_request('POST', '/api/auth/logout/')
    
    response = client.post('/api/auth/logout/')
    print_response(response)
    
    assert response.status_code == 200
    assert response.json()['success'] == True
    print("   ✓ Logout successful")
    
    # Test 2: Try to access protected endpoint after logout
    print("\n❌ Test 2: Access Protected Endpoint After Logout")
    print_request('GET', '/api/auth/me/')
    
    response = client.get('/api/auth/me/')
    print_response(response)
    
    assert response.status_code in [302, 401]
    print("   ✓ Session correctly terminated")


def test_complete_flow():
    """Test complete authentication flow"""
    print_section("6. Testing Complete Authentication Flow")
    
    client = Client()
    
    # Clean up
    User.objects.filter(username='flow_test_user').delete()
    
    # Step 1: Register
    print("\n📝 Step 1: Register New User")
    data = {
        'username': 'flow_test_user',
        'email': 'flow@example.com',
        'password': 'FlowPass123'
    }
    response = client.post(
        '/api/auth/register/',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 201
    print("   ✓ User registered")
    
    # Step 2: Login
    print("\n🔐 Step 2: Login")
    data = {
        'username': 'flow_test_user',
        'password': 'FlowPass123'
    }
    response = client.post(
        '/api/auth/login/',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 200
    print("   ✓ User logged in")
    
    # Step 3: Get current user
    print("\n👤 Step 3: Get Current User")
    response = client.get('/api/auth/me/')
    assert response.status_code == 200
    user_data = response.json()['user']
    print(f"   ✓ Current user: {user_data['username']}")
    print(f"   - Balance: {user_data['balance']}")
    
    # Step 4: Get profile
    print("\n📊 Step 4: Get Profile")
    response = client.get('/api/auth/profile/')
    assert response.status_code == 200
    profile_data = response.json()['profile']
    print(f"   ✓ Profile retrieved")
    print(f"   - Username: {profile_data['user']['username']}")
    print(f"   - Email: {profile_data['user']['email']}")
    
    # Step 5: Logout
    print("\n🚪 Step 5: Logout")
    response = client.post('/api/auth/logout/')
    assert response.status_code == 200
    print("   ✓ User logged out")
    
    # Step 6: Verify logout
    print("\n🔒 Step 6: Verify Logout")
    response = client.get('/api/auth/me/')
    assert response.status_code in [302, 401]
    print("   ✓ Access denied after logout")
    
    # Cleanup
    User.objects.filter(username='flow_test_user').delete()


def cleanup():
    """Clean up test data"""
    print_section("7. Cleanup")
    
    deleted_count = User.objects.filter(username__startswith='api_test_').delete()[0]
    print(f"\n✓ Deleted {deleted_count} test users")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Authentication API Test Suite")
    print("=" * 60)
    
    try:
        test_registration()
        client = test_login()
        test_current_user(client)
        test_profile(client)
        test_logout(client)
        test_complete_flow()
        cleanup()
        
        print("\n" + "=" * 60)
        print("  ✓ All API Tests Completed Successfully!")
        print("=" * 60 + "\n")
        
    except AssertionError as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
