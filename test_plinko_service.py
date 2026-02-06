"""
Test script for Plinko Game Service.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from decimal import Decimal
from users.models import User
from games.models import PlinkoGame
from games.services.plinko_service import PlinkoGameService
from wallet.services import WalletService, InsufficientFundsError
from django.core.exceptions import ValidationError


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_create_game():
    """Test creating Plinko game"""
    print_section("1. Testing Create Game")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='plinko_test_user',
        defaults={
            'email': 'plinko@example.com',
            'password': 'testpass123'
        }
    )
    
    if created:
        print(f"\n✓ Created test user: {user.username}")
    else:
        print(f"\n✓ Using existing user: {user.username}")
    
    # Ensure user has balance
    balance = WalletService.get_balance(user)
    if balance < Decimal('100.00'):
        WalletService.deposit(user, Decimal('1000.00'))
        print(f"  ✓ Added demo balance: 1000.00")
    
    # Test 1: Create valid game
    print("\n🎮 Test 1: Create Valid Game")
    bet_amount = Decimal('10.00')
    row_count = 11  # Changed from 14 to 11
    risk_level = 'medium'
    
    game = PlinkoGameService.create_game(
        user=user,
        bet_amount=bet_amount,
        row_count=row_count,
        risk_level=risk_level
    )
    
    print(f"  ✓ Game created: ID={game.id}")
    print(f"  - Bet amount: {game.bet_amount}")
    print(f"  - Row count: {game.row_count}")
    print(f"  - Risk level: {game.get_risk_level_display()}")
    print(f"  - Completed: {game.is_completed()}")
    
    assert game.bet_amount == bet_amount
    assert game.row_count == row_count
    assert game.risk_level == risk_level
    assert not game.is_completed()
    print("  ✓ Game created successfully")
    
    # Test 2: Invalid row count
    print("\n❌ Test 2: Invalid Row Count")
    try:
        PlinkoGameService.create_game(user, Decimal('10.00'), 10, 'medium')  # 10 is not valid
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 3: Invalid risk level
    print("\n❌ Test 3: Invalid Risk Level")
    try:
        PlinkoGameService.create_game(user, Decimal('10.00'), 11, 'invalid')  # Changed from 14 to 11
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 4: Invalid bet amount
    print("\n❌ Test 4: Invalid Bet Amount")
    try:
        PlinkoGameService.create_game(user, Decimal('0.00'), 11, 'medium')  # Changed from 14 to 11
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_drop_ball():
    """Test dropping ball"""
    print_section("2. Testing Drop Ball")
    
    user = User.objects.get(username='plinko_test_user')
    
    # Ensure balance
    balance = WalletService.get_balance(user)
    if balance < Decimal('100.00'):
        WalletService.deposit(user, Decimal('1000.00'))
    
    # Test 1: Drop ball successfully
    print("\n🎯 Test 1: Drop Ball Successfully")
    bet_amount = Decimal('10.00')
    row_count = 11  # Changed from 14 to 11
    risk_level = 'medium'
    
    game = PlinkoGameService.create_game(user, bet_amount, row_count, risk_level)
    print(f"  ✓ Game created: ID={game.id}")
    
    result = PlinkoGameService.drop_ball(game)
    
    print(f"  ✓ Ball dropped successfully")
    print(f"  - Ball path: {result['ball_path']}")
    print(f"  - Bucket index: {result['bucket_index']}")
    print(f"  - Multiplier: {result['multiplier']}x")
    print(f"  - Winnings: {result['winnings']} ₽")
    
    # Verify game updated
    game.refresh_from_db()
    assert game.is_completed()
    assert game.ball_path == result['ball_path']
    assert game.bucket_index == result['bucket_index']
    assert game.final_multiplier == result['multiplier']
    print("  ✓ Game state updated correctly")
    
    # Test 2: Cannot drop ball twice
    print("\n❌ Test 2: Cannot Drop Ball Twice")
    try:
        PlinkoGameService.drop_ball(game)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 3: Insufficient funds
    print("\n❌ Test 3: Insufficient Funds")
    # Drain balance
    current_balance = WalletService.get_balance(user)
    if current_balance > Decimal('5.00'):
        # Create games to drain balance
        while WalletService.get_balance(user) > Decimal('5.00'):
            try:
                g = PlinkoGameService.create_game(user, Decimal('10.00'), 11, 'medium')  # Changed from 14 to 11
                PlinkoGameService.drop_ball(g)
            except InsufficientFundsError:
                break
    
    try:
        g = PlinkoGameService.create_game(user, Decimal('10.00'), 11, 'medium')  # Changed from 14 to 11
        PlinkoGameService.drop_ball(g)
        print("  ✗ Should have raised InsufficientFundsError")
    except InsufficientFundsError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Restore balance
    WalletService.deposit(user, Decimal('1000.00'))


def test_multipliers():
    """Test multiplier retrieval"""
    print_section("3. Testing Multipliers")
    
    # Test 1: Get valid multiplier
    print("\n✓ Test 1: Get Valid Multiplier")
    mult = PlinkoGameService.get_multiplier('medium', 11, 5)  # Changed from 14, 7 to 11, 5
    print(f"  - Medium risk, 11 rows, bucket 5: {mult}x")
    assert mult > 0
    print("  ✓ Multiplier retrieved successfully")
    
    # Test 2: Invalid risk level
    print("\n❌ Test 2: Invalid Risk Level")
    try:
        PlinkoGameService.get_multiplier('invalid', 11, 5)  # Changed from 14, 7 to 11, 5
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 3: Invalid row count
    print("\n❌ Test 3: Invalid Row Count")
    try:
        PlinkoGameService.get_multiplier('medium', 20, 7)  # 20 is not valid
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 4: Print all multipliers
    print("\n📊 Test 4: All Multipliers")
    for risk in ['low', 'medium', 'high']:
        print(f"\n  {risk.upper()} Risk:")
        for rows in [5, 9, 11, 13, 15]:  # Changed from [12, 13, 14, 15, 16] to [5, 9, 11, 13, 15]
            mults = PlinkoGameService.MULTIPLIERS[risk][rows]
            max_mult = max(mults)
            min_mult = min(mults)
            print(f"    {rows} rows: Min {min_mult}x, Max {max_mult}x, Buckets: {len(mults)}")


def test_ball_path_simulation():
    """Test ball path simulation"""
    print_section("4. Testing Ball Path Simulation")
    
    print("\n🎲 Test 1: Simulate Multiple Paths")
    row_count = 11  # Changed from 14 to 11
    
    # Simulate 10 paths
    paths = []
    buckets = []
    for i in range(10):
        path, bucket = PlinkoGameService.simulate_ball_path(row_count)
        paths.append(path)
        buckets.append(bucket)
        print(f"  Path {i+1}: {path} -> Bucket {bucket}")
    
    # Verify path properties
    for path, bucket in zip(paths, buckets):
        assert len(path) == row_count
        assert all(p in [0, 1] for p in path)
        assert bucket == sum(path)
        assert 0 <= bucket <= row_count
    
    print(f"\n  ✓ All paths valid")
    print(f"  - Average bucket: {sum(buckets) / len(buckets):.2f}")
    print(f"  - Expected (center): {row_count / 2}")


def test_auto_play():
    """Test auto-play functionality"""
    print_section("5. Testing Auto-Play")
    
    user = User.objects.get(username='plinko_test_user')
    
    # Ensure balance
    balance = WalletService.get_balance(user)
    if balance < Decimal('500.00'):
        WalletService.deposit(user, Decimal('1000.00'))
    
    # Test 1: Auto-play 5 drops
    print("\n🔄 Test 1: Auto-Play 5 Drops")
    bet_amount = Decimal('10.00')
    row_count = 11  # Changed from 14 to 11
    risk_level = 'medium'
    drop_count = 5
    
    initial_balance = WalletService.get_balance(user)
    print(f"  - Initial balance: {initial_balance} ₽")
    
    results = PlinkoGameService.auto_play(
        user=user,
        bet_amount=bet_amount,
        row_count=row_count,
        risk_level=risk_level,
        drop_count=drop_count
    )
    
    final_balance = WalletService.get_balance(user)
    print(f"  - Final balance: {final_balance} ₽")
    print(f"  - Drops executed: {len(results)}")
    
    total_winnings = sum(r['winnings'] for r in results)
    print(f"  - Total winnings: {total_winnings} ₽")
    
    for i, r in enumerate(results, 1):
        print(f"    Drop {i}: Bucket {r['bucket_index']}, {r['multiplier']}x, {r['winnings']} ₽")
    
    assert len(results) == drop_count
    print("  ✓ Auto-play completed successfully")
    
    # Test 2: Invalid drop count
    print("\n❌ Test 2: Invalid Drop Count")
    try:
        PlinkoGameService.auto_play(user, Decimal('10.00'), 14, 'medium', 0)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 3: Too many drops
    print("\n❌ Test 3: Too Many Drops")
    try:
        PlinkoGameService.auto_play(user, Decimal('10.00'), 14, 'medium', 101)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_risk_levels():
    """Test different risk levels"""
    print_section("6. Testing Risk Levels")
    
    user = User.objects.get(username='plinko_test_user')
    
    # Ensure balance
    balance = WalletService.get_balance(user)
    if balance < Decimal('500.00'):
        WalletService.deposit(user, Decimal('1000.00'))
    
    bet_amount = Decimal('10.00')
    row_count = 11  # Changed from 14 to 11
    
    for risk in ['low', 'medium', 'high']:
        print(f"\n🎯 Testing {risk.upper()} Risk")
        
        # Play 5 games
        results = []
        for _ in range(5):
            game = PlinkoGameService.create_game(user, bet_amount, row_count, risk)
            result = PlinkoGameService.drop_ball(game)
            results.append(result)
        
        multipliers = [r['multiplier'] for r in results]
        winnings = [r['winnings'] for r in results]
        
        print(f"  - Multipliers: {[float(m) for m in multipliers]}")
        print(f"  - Average multiplier: {sum(multipliers) / len(multipliers):.2f}x")
        print(f"  - Total winnings: {sum(winnings)} ₽")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  PLINKO GAME SERVICE - TEST SUITE")
    print("=" * 60)
    
    try:
        test_create_game()
        test_drop_ball()
        test_multipliers()
        test_ball_path_simulation()
        test_auto_play()
        test_risk_levels()
        
        print("\n" + "=" * 60)
        print("  ✓ ALL TESTS PASSED")
        print("=" * 60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        raise


if __name__ == '__main__':
    run_all_tests()
