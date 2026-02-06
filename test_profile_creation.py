"""
Test script to verify Profile is created automatically when User is created.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from users.models import User, Profile
from decimal import Decimal

def test_profile_creation():
    print("=" * 60)
    print("Testing Profile Auto-Creation")
    print("=" * 60)
    
    # Clean up test user if exists
    test_username = 'test_user_profile'
    User.objects.filter(username=test_username).delete()
    
    # Create a new user
    print(f"\n1. Creating user: {test_username}")
    user = User.objects.create_user(
        username=test_username,
        email='test@example.com',
        password='testpass123'
    )
    print(f"   ✓ User created: {user}")
    
    # Check if profile was created automatically
    print(f"\n2. Checking if Profile was created automatically...")
    try:
        profile = user.profile
        print(f"   ✓ Profile exists: {profile}")
        print(f"   - Balance: {profile.balance}")
        print(f"   - Total Wagered: {profile.total_wagered}")
        print(f"   - Total Won: {profile.total_won}")
        print(f"   - Created at: {profile.created_at}")
        
        # Verify default values
        assert profile.balance == Decimal('1000.00'), "Default balance should be 1000.00"
        assert profile.total_wagered == Decimal('0.00'), "Default total_wagered should be 0.00"
        assert profile.total_won == Decimal('0.00'), "Default total_won should be 0.00"
        print(f"\n   ✓ All default values are correct!")
        
    except Profile.DoesNotExist:
        print(f"   ✗ Profile was NOT created automatically!")
        return False
    
    # Test balance constraint
    print(f"\n3. Testing balance constraint (balance >= 0)...")
    try:
        profile.balance = Decimal('-100.00')
        profile.save()
        print(f"   ✗ Constraint failed! Negative balance was allowed.")
        return False
    except Exception as e:
        print(f"   ✓ Constraint works! Negative balance rejected.")
        print(f"   Error: {type(e).__name__}")
    
    # Clean up
    print(f"\n4. Cleaning up test data...")
    user.delete()
    print(f"   ✓ Test user deleted")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    test_profile_creation()
