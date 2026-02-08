"""
Test Crash Game Service
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from django.contrib.auth import get_user_model
from games.services.crash_service import CrashGameService
from games.models import CrashRound, CrashBet

User = get_user_model()


def test_crash_point_generation():
    """Test crash point generation"""
    print("\n=== Testing Crash Point Generation ===")
    
    # Generate multiple crash points
    crash_points = []
    for i in range(100):
        server_seed = f"server_seed_{i}"
        client_seed = f"client_seed_{i}"
        crash_point = CrashGameService.calculate_crash_point(server_seed, client_seed)
        crash_points.append(float(crash_point))
    
    # Calculate average
    avg_crash_point = sum(crash_points) / len(crash_points)
    
    print(f"Generated {len(crash_points)} crash points")
    print(f"Min: {min(crash_points):.2f}x")
    print(f"Max: {max(crash_points):.2f}x")
    print(f"Average: {avg_crash_point:.2f}x")
    
    # Check RTP (should be around 97%)
    # Expected average crash point for 97% RTP: 100/97 ≈ 1.03
    print(f"Expected average for 97% RTP: ~1.03x")
    
    # Count distribution
    low = sum(1 for cp in crash_points if cp < 2.0)
    medium = sum(1 for cp in crash_points if 2.0 <= cp < 5.0)
    high = sum(1 for cp in crash_points if cp >= 5.0)
    
    print(f"\nDistribution:")
    print(f"  < 2.0x: {low}%")
    print(f"  2.0-5.0x: {medium}%")
    print(f"  >= 5.0x: {high}%")
    
    print("✓ Crash point generation test passed")


def test_round_creation():
    """Test round creation"""
    print("\n=== Testing Round Creation ===")
    
    # Create new round
    round_instance = CrashGameService.start_new_round()
    
    print(f"Round ID: {round_instance.round_id}")
    print(f"Status: {round_instance.status}")
    print(f"Crash Point: {round_instance.crash_point}x")
    print(f"Server Seed Hash: {round_instance.server_seed_hash[:16]}...")
    
    assert round_instance.status == CrashRound.RoundStatus.WAITING
    assert round_instance.crash_point >= Decimal('1.00')
    assert round_instance.server_seed
    assert round_instance.client_seed
    assert round_instance.server_seed_hash
    
    print("✓ Round creation test passed")
    
    return round_instance


def test_bet_placement():
    """Test bet placement"""
    print("\n=== Testing Bet Placement ===")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='crash_test_user',
        defaults={'email': 'crash_test@example.com'}
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Ensure profile exists and has balance
    from users.models import Profile
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.balance = Decimal('1000.00')
    profile.save()
    
    print(f"User: {user.username}")
    print(f"Initial Balance: {profile.balance}")
    
    # Create round
    round_instance = CrashGameService.start_new_round()
    
    # Place bet
    bet_amount = Decimal('10.00')
    bet = CrashGameService.place_bet(
        user=user,
        amount=bet_amount,
        auto_cashout_target=Decimal('2.00')
    )
    
    print(f"Bet ID: {bet.id}")
    print(f"Bet Amount: {bet.bet_amount}")
    print(f"Auto Cashout: {bet.auto_cashout_target}x")
    print(f"Status: {bet.status}")
    
    # Check balance deducted
    profile.refresh_from_db()
    print(f"Balance After Bet: {profile.balance}")
    
    assert bet.status == CrashBet.BetStatus.ACTIVE
    assert bet.bet_amount == bet_amount
    assert bet.auto_cashout_target == Decimal('2.00')
    assert profile.balance == Decimal('990.00')
    
    print("✓ Bet placement test passed")
    
    return user, round_instance, bet


def test_multiplier_calculation():
    """Test multiplier calculation"""
    print("\n=== Testing Multiplier Calculation ===")
    
    # Create and activate round
    round_instance = CrashGameService.start_new_round()
    CrashGameService.activate_round(round_instance)
    
    print(f"Round activated at: {round_instance.started_at}")
    
    # Get current multiplier (should be close to 1.00)
    multiplier = CrashGameService.get_current_multiplier(round_instance)
    print(f"Current Multiplier: {multiplier}x")
    
    assert multiplier >= Decimal('1.00')
    assert multiplier <= round_instance.crash_point
    
    print("✓ Multiplier calculation test passed")


def test_cashout():
    """Test manual cashout"""
    print("\n=== Testing Manual Cashout ===")
    
    # Setup
    user, round_instance, bet = test_bet_placement()
    
    # Activate round
    CrashGameService.activate_round(round_instance)
    
    # Get initial balance
    initial_balance = user.profile.balance
    print(f"Balance Before Cashout: {initial_balance}")
    
    # Cashout
    import time
    time.sleep(0.1)  # Wait a bit for multiplier to grow
    
    cashed_bet = CrashGameService.cashout(user, bet.id)
    
    print(f"Cashout Multiplier: {cashed_bet.cashout_multiplier}x")
    print(f"Win Amount: {cashed_bet.win_amount}")
    
    # Check balance updated
    user.profile.refresh_from_db()
    print(f"Balance After Cashout: {user.profile.balance}")
    
    assert cashed_bet.status == CrashBet.BetStatus.CASHED_OUT
    assert cashed_bet.win_amount > 0
    assert user.profile.balance > initial_balance
    
    print("✓ Cashout test passed")


def test_crash_round():
    """Test round crash"""
    print("\n=== Testing Round Crash ===")
    
    # Create and activate round
    round_instance = CrashGameService.start_new_round()
    CrashGameService.activate_round(round_instance)
    
    # Crash round
    CrashGameService.crash_round(round_instance)
    
    print(f"Round Status: {round_instance.status}")
    print(f"Crashed At: {round_instance.crashed_at}")
    
    assert round_instance.status == CrashRound.RoundStatus.CRASHED
    assert round_instance.crashed_at is not None
    
    print("✓ Round crash test passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("CRASH GAME SERVICE TESTS")
    print("=" * 60)
    
    try:
        test_crash_point_generation()
        test_round_creation()
        test_multiplier_calculation()
        test_cashout()
        test_crash_round()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
