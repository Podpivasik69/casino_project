"""
Test the complete crash bet flow with a real user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from users.models import User, Profile
from games.services.crash_service import CrashGameService
from decimal import Decimal

print("=" * 60)
print("CRASH BET FLOW TEST")
print("=" * 60)

# Create or get test user
print("\n1. Creating/getting test user...")
user, created = User.objects.get_or_create(
    username='crash_test_user',
    defaults={'email': 'crash@test.com'}
)

if created:
    user.set_password('test123')
    user.save()
    print(f"✓ User created: {user.username}")
else:
    print(f"✓ User exists: {user.username}")

# Ensure profile exists with balance
profile, _ = Profile.objects.get_or_create(user=user)
if profile.balance < 100:
    profile.balance = Decimal('1000.00')
    profile.save()
print(f"✓ Balance: {profile.balance} ₽")

# Create a round
print("\n2. Creating round...")
round_instance = CrashGameService.start_new_round()
print(f"✓ Round created: {round_instance.round_id}")
print(f"  Status: {round_instance.status}")
print(f"  Crash Point: {round_instance.crash_point}x")

# Try to place a bet
print("\n3. Placing bet...")
try:
    bet = CrashGameService.place_bet(
        user=user,
        amount=Decimal('10.00'),
        auto_cashout_target=Decimal('2.00')
    )
    print(f"✓ Bet placed successfully!")
    print(f"  Bet ID: {bet.id}")
    print(f"  Amount: {bet.bet_amount} ₽")
    print(f"  Auto cashout: {bet.auto_cashout_target}x")
    
    # Check balance
    profile.refresh_from_db()
    print(f"  New balance: {profile.balance} ₽")
    
except Exception as e:
    print(f"✗ Error placing bet: {e}")
    import traceback
    traceback.print_exc()

# Activate round
print("\n4. Activating round...")
try:
    CrashGameService.activate_round(round_instance)
    round_instance.refresh_from_db()
    print(f"✓ Round activated")
    print(f"  Status: {round_instance.status}")
    
    # Get current multiplier
    multiplier = CrashGameService.get_current_multiplier(round_instance)
    print(f"  Current multiplier: {multiplier}x")
    
except Exception as e:
    print(f"✗ Error activating round: {e}")

# Try cashout
print("\n5. Testing cashout...")
try:
    bet.refresh_from_db()
    if bet.is_active():
        cashed_bet = CrashGameService.cashout(user=user, bet_id=bet.id)
        print(f"✓ Cashed out successfully!")
        print(f"  Cashout multiplier: {cashed_bet.cashout_multiplier}x")
        print(f"  Win amount: {cashed_bet.win_amount} ₽")
        
        # Check balance
        profile.refresh_from_db()
        print(f"  New balance: {profile.balance} ₽")
    else:
        print(f"⚠ Bet is not active (status: {bet.status})")
        
except Exception as e:
    print(f"✗ Error cashing out: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✓ TEST COMPLETE")
print("=" * 60)
print("\nNow try accessing the game in browser:")
print("http://localhost:8000/crash/")
print("\nLogin with:")
print("  Username: crash_test_user")
print("  Password: test123")
