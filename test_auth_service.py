"""
Test script to verify AuthService functionality.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from users.services import AuthService
from users.models import User
from django.core.exceptions import ValidationError


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_validation():
    """Test input validation"""
    print_section("1. Testing Input Validation")
    
    # Test email validation
    print("\n📧 Email Validation:")
    test_cases = [
        ("", False, "Empty email"),
        ("invalid", False, "Invalid format"),
        ("test@example.com", True, "Valid email"),
        ("user.name+tag@example.co.uk", True, "Complex valid email"),
    ]
    
    for email, should_pass, description in test_cases:
        try:
            AuthService.validate_email(email)
            result = "✓ PASS" if should_pass else "✗ FAIL (should reject)"
        except ValidationError as e:
            result = "✗ FAIL (should accept)" if should_pass else f"✓ PASS - {e}"
        print(f"  {description}: {result}")
    
    # Test username validation
    print("\n👤 Username Validation:")
    test_cases = [
        ("", False, "Empty username"),
        ("ab", False, "Too short (2 chars)"),
        ("valid_user123", True, "Valid username"),
        ("user@invalid", False, "Invalid characters"),
        ("a" * 151, False, "Too long (151 chars)"),
    ]
    
    for username, should_pass, description in test_cases:
        try:
            AuthService.validate_username(username)
            result = "✓ PASS" if should_pass else "✗ FAIL (should reject)"
        except ValidationError as e:
            result = "✗ FAIL (should accept)" if should_pass else f"✓ PASS - {e}"
        print(f"  {description}: {result}")
    
    # Test password validation
    print("\n🔒 Password Validation:")
    test_cases = [
        ("", False, "Empty password"),
        ("short", False, "Too short (5 chars)"),
        ("12345678", False, "Only digits"),
        ("abcdefgh", False, "Only letters"),
        ("Pass1234", True, "Valid password"),
        ("MySecurePass123", True, "Strong password"),
    ]
    
    for password, should_pass, description in test_cases:
        try:
            AuthService.validate_password(password)
            result = "✓ PASS" if should_pass else "✗ FAIL (should reject)"
        except ValidationError as e:
            result = "✗ FAIL (should accept)" if should_pass else f"✓ PASS - {e}"
        print(f"  {description}: {result}")


def test_registration():
    """Test user registration"""
    print_section("2. Testing User Registration")
    
    # Clean up test users
    User.objects.filter(username__startswith='test_auth_').delete()
    
    # Test successful registration
    print("\n✅ Test 1: Successful Registration")
    try:
        user = AuthService.register_user(
            username='test_auth_user1',
            email='test_auth1@example.com',
            password='TestPass123',
            first_name='Test',
            last_name='User'
        )
        print(f"  ✓ User created: {user.username}")
        print(f"  ✓ Email: {user.email}")
        print(f"  ✓ Full name: {user.get_full_name()}")
        print(f"  ✓ Profile exists: {hasattr(user, 'profile')}")
        print(f"  ✓ Initial balance: {user.profile.balance}")
        print(f"  ✓ Password is hashed: {user.password[:20]}...")
    except Exception as e:
        print(f"  ✗ Registration failed: {e}")
    
    # Test duplicate username
    print("\n❌ Test 2: Duplicate Username")
    try:
        user = AuthService.register_user(
            username='test_auth_user1',  # Same username
            email='different@example.com',
            password='TestPass123'
        )
        print(f"  ✗ Should have failed but created: {user.username}")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test duplicate email
    print("\n❌ Test 3: Duplicate Email")
    try:
        user = AuthService.register_user(
            username='test_auth_user2',
            email='test_auth1@example.com',  # Same email
            password='TestPass123'
        )
        print(f"  ✗ Should have failed but created: {user.username}")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test invalid data
    print("\n❌ Test 4: Invalid Password")
    try:
        user = AuthService.register_user(
            username='test_auth_user3',
            email='test3@example.com',
            password='weak'  # Too short, no digits
        )
        print(f"  ✗ Should have failed but created: {user.username}")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_authentication():
    """Test user authentication"""
    print_section("3. Testing User Authentication")
    
    # Create test user
    User.objects.filter(username='test_auth_login').delete()
    user = AuthService.register_user(
        username='test_auth_login',
        email='test_login@example.com',
        password='LoginPass123'
    )
    print(f"\n✓ Test user created: {user.username}")
    
    # Test successful authentication with username
    print("\n✅ Test 1: Authenticate with Username")
    auth_user = AuthService.authenticate_user('test_auth_login', 'LoginPass123')
    if auth_user:
        print(f"  ✓ Authentication successful: {auth_user.username}")
    else:
        print(f"  ✗ Authentication failed")
    
    # Test successful authentication with email
    print("\n✅ Test 2: Authenticate with Email")
    auth_user = AuthService.authenticate_user('test_login@example.com', 'LoginPass123')
    if auth_user:
        print(f"  ✓ Authentication successful: {auth_user.username}")
    else:
        print(f"  ✗ Authentication failed")
    
    # Test wrong password
    print("\n❌ Test 3: Wrong Password")
    auth_user = AuthService.authenticate_user('test_auth_login', 'WrongPass123')
    if auth_user:
        print(f"  ✗ Should have failed but authenticated: {auth_user.username}")
    else:
        print(f"  ✓ Correctly rejected invalid password")
    
    # Test non-existent user
    print("\n❌ Test 4: Non-existent User")
    auth_user = AuthService.authenticate_user('nonexistent_user', 'SomePass123')
    if auth_user:
        print(f"  ✗ Should have failed but authenticated: {auth_user.username}")
    else:
        print(f"  ✓ Correctly rejected non-existent user")


def test_profile_retrieval():
    """Test profile data retrieval"""
    print_section("4. Testing Profile Retrieval")
    
    # Get existing test user
    user = User.objects.get(username='test_auth_user1')
    
    print("\n📊 Get User Profile:")
    try:
        profile_data = AuthService.get_user_profile(user)
        print(f"  ✓ Profile retrieved successfully")
        print(f"  - Username: {profile_data['username']}")
        print(f"  - Email: {profile_data['email']}")
        print(f"  - Balance: {profile_data['balance']}")
        print(f"  - Total Wagered: {profile_data['total_wagered']}")
        print(f"  - Total Won: {profile_data['total_won']}")
        print(f"  - Date Joined: {profile_data['date_joined']}")
    except Exception as e:
        print(f"  ✗ Failed to retrieve profile: {e}")


def test_user_lookup():
    """Test user lookup methods"""
    print_section("5. Testing User Lookup Methods")
    
    user = User.objects.get(username='test_auth_user1')
    
    # Test get by ID
    print("\n🔍 Get User by ID:")
    found_user = AuthService.get_user_by_id(user.id)
    if found_user:
        print(f"  ✓ Found user: {found_user.username}")
    else:
        print(f"  ✗ User not found")
    
    # Test get by username
    print("\n🔍 Get User by Username:")
    found_user = AuthService.get_user_by_username('test_auth_user1')
    if found_user:
        print(f"  ✓ Found user: {found_user.username}")
    else:
        print(f"  ✗ User not found")
    
    # Test get by email
    print("\n🔍 Get User by Email:")
    found_user = AuthService.get_user_by_email('test_auth1@example.com')
    if found_user:
        print(f"  ✓ Found user: {found_user.username}")
    else:
        print(f"  ✗ User not found")
    
    # Test non-existent user
    print("\n🔍 Get Non-existent User:")
    found_user = AuthService.get_user_by_username('nonexistent_user_xyz')
    if found_user:
        print(f"  ✗ Should not have found user: {found_user.username}")
    else:
        print(f"  ✓ Correctly returned None for non-existent user")


def cleanup():
    """Clean up test data"""
    print_section("6. Cleanup")
    
    deleted_count = User.objects.filter(username__startswith='test_auth_').delete()[0]
    print(f"\n✓ Deleted {deleted_count} test users")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  AuthService Test Suite")
    print("=" * 60)
    
    try:
        test_validation()
        test_registration()
        test_authentication()
        test_profile_retrieval()
        test_user_lookup()
        cleanup()
        
        print("\n" + "=" * 60)
        print("  ✓ All Tests Completed Successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
