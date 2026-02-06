"""
Test script for Mines Game Service.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from decimal import Decimal
from users.models import User
from games.models import MinesGame
from games.services.mines_service import MinesGameService
from wallet.services import WalletService, InsufficientFundsError
from django.core.exceptions import ValidationError


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_create_game():
    """Test creating Mines game"""
    print_section("1. Testing Create Game")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='mines_test_user',
        defaults={
            'email': 'mines@example.com',
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
    mine_count = 5
    
    game = MinesGameService.create_game(
        user=user,
        bet_amount=bet_amount,
        mine_count=mine_count
    )
    
    print(f"  ✓ Game created: ID={game.id}")
    print(f"  - Bet amount: {game.bet_amount}")
    print(f"  - Mine count: {game.mine_count}")
    print(f"  - State: {game.get_state_display()}")
    print(f"  - Server seed hash: {game.server_seed_hash[:32]}...")
    print(f"  - Client seed: {game.client_seed[:32]}...")
    print(f"  - Nonce: {game.nonce}")
    print(f"  - Mine positions: {len(game.mine_positions)} mines")
    
    assert game.state == MinesGame.GameState.ACTIVE
    assert game.bet_amount == bet_amount
    assert game.mine_count == mine_count
    assert len(game.mine_positions) == mine_count
    assert game.current_multiplier == Decimal('1.0')
    print("  ✓ Game created successfully")
    
    # Test 2: Invalid mine count
    print("\n❌ Test 2: Invalid Mine Count")
    try:
        MinesGameService.create_game(user, Decimal('10.00'), 2)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 3: Invalid bet amount
    print("\n❌ Test 3: Invalid Bet Amount")
    try:
        MinesGameService.create_game(user, Decimal('0.00'), 5)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 4: Insufficient funds
    print("\n❌ Test 4: Insufficient Funds")
    try:
        huge_bet = WalletService.get_balance(user) + Decimal('1000.00')
        MinesGameService.create_game(user, huge_bet, 5)
        print("  ✗ Should have raised InsufficientFundsError")
    except InsufficientFundsError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_calculate_multiplier():
    """Test multiplier calculation"""
    print_section("2. Testing Multiplier Calculation")
    
    # Test various scenarios
    test_cases = [
        (5, 0, Decimal('1.00')),
        (5, 1, Decimal('1.25')),
        (5, 2, Decimal('1.58')),
        (5, 3, Decimal('2.02')),
        (10, 1, Decimal('1.67')),
        (10, 2, Decimal('2.86')),
        (20, 1, Decimal('5.00')),
        (20, 2, Decimal('30.00')),  # (25/5) * (24/4) = 5.0 * 6.0 = 30.0
    ]
    
    print("\n📊 Multiplier Test Cases:")
    for mine_count, opened, expected in test_cases:
        result = MinesGameService.calculate_multiplier(mine_count, opened)
        print(f"  Mines={mine_count}, Opened={opened}: {result}x (expected ~{expected}x)")
        
        # Allow small difference due to rounding
        assert abs(result - expected) < Decimal('0.1'), f"Multiplier mismatch: {result} vs {expected}"
    
    print("  ✓ All multiplier calculations correct")


def test_open_cell():
    """Test opening cells"""
    print_section("3. Testing Open Cell")
    
    user = User.objects.get(username='mines_test_user')
    
    # Create game
    game = MinesGameService.create_game(user, Decimal('10.00'), 5)
    
    print(f"\n🎮 Created game {game.id} with {game.mine_count} mines")
    print(f"  Mine positions: {game.mine_positions}")
    
    # Test 1: Open safe cell
    print("\n✅ Test 1: Open Safe Cell")
    
    # Find a safe cell
    safe_cell = None
    for row in range(5):
        for col in range(5):
            if [row, col] not in game.mine_positions:
                safe_cell = (row, col)
                break
        if safe_cell:
            break
    
    result = MinesGameService.open_cell(game, safe_cell[0], safe_cell[1])
    
    print(f"  Opened cell ({safe_cell[0]}, {safe_cell[1]})")
    print(f"  - Is mine: {result['is_mine']}")
    print(f"  - Multiplier: {result['multiplier']}x")
    print(f"  - Game state: {result['game_state']}")
    print(f"  - Opened count: {result['opened_count']}")
    
    assert result['is_mine'] == False
    assert result['multiplier'] > Decimal('1.0')
    assert result['game_state'] == MinesGame.GameState.ACTIVE
    print("  ✓ Safe cell opened successfully")
    
    # Test 2: Open mine
    print("\n💣 Test 2: Open Mine")
    
    # Create new game with many mines to increase chance
    game2 = MinesGameService.create_game(user, Decimal('10.00'), 20)
    
    # Try to open first mine position
    mine_pos = game2.mine_positions[0]
    
    print(f"  Mine positions (first 5): {game2.mine_positions[:5]}")
    print(f"  Opening cell at ({mine_pos[0]}, {mine_pos[1]})")
    
    result = MinesGameService.open_cell(game2, mine_pos[0], mine_pos[1])
    
    print(f"  - Is mine: {result['is_mine']}")
    print(f"  - Game state: {result['game_state']}")
    
    assert result['is_mine'] == True, "Should have hit a mine"
    assert result['game_state'] == MinesGame.GameState.LOST
    assert result['multiplier'] == Decimal('0.0')
    print(f"  - Mine positions revealed: {len(result['mine_positions'])} mines")
    print("  ✓ Mine hit correctly")
    
    # Test 3: Open already opened cell
    print("\n❌ Test 3: Open Already Opened Cell")
    try:
        MinesGameService.open_cell(game, safe_cell[0], safe_cell[1])
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 4: Open cell in ended game
    print("\n❌ Test 4: Open Cell in Ended Game")
    try:
        MinesGameService.open_cell(game2, 0, 0)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_cashout():
    """Test cashing out"""
    print_section("4. Testing Cashout")
    
    user = User.objects.get(username='mines_test_user')
    
    # Get balance before creating game
    balance_before_game = WalletService.get_balance(user)
    
    # Create game and open safe cells
    game = MinesGameService.create_game(user, Decimal('10.00'), 5)
    
    print(f"\n🎮 Created game {game.id}")
    print(f"  Balance before game: {balance_before_game}")
    print(f"  Bet amount: {game.bet_amount}")
    
    # Open 2 safe cells
    opened_count = 0
    for row in range(5):
        for col in range(5):
            if [row, col] not in game.mine_positions and opened_count < 2:
                MinesGameService.open_cell(game, row, col)
                opened_count += 1
    
    game.refresh_from_db()
    print(f"  Opened {opened_count} safe cells")
    print(f"  Current multiplier: {game.current_multiplier}x")
    
    # Test 1: Valid cashout
    print("\n💰 Test 1: Valid Cashout")
    winnings = MinesGameService.cashout(game)
    
    print(f"  ✓ Cashed out successfully")
    print(f"  - Winnings: {winnings}")
    print(f"  - Expected: {game.bet_amount * game.current_multiplier}")
    
    game.refresh_from_db()
    assert game.state == MinesGame.GameState.CASHED_OUT
    assert game.ended_at is not None
    
    # Check balance updated
    user.refresh_from_db()
    new_balance = WalletService.get_balance(user)
    # Balance should be: initial - bet + winnings
    expected_balance = balance_before_game - game.bet_amount + winnings
    print(f"  - New balance: {new_balance}")
    print(f"  - Expected balance: {expected_balance}")
    
    assert new_balance == expected_balance
    print("  ✓ Balance updated correctly")
    
    # Test 2: Cashout without opening cells
    print("\n❌ Test 2: Cashout Without Opening Cells")
    game2 = MinesGameService.create_game(user, Decimal('10.00'), 5)
    
    try:
        MinesGameService.cashout(game2)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 3: Cashout ended game
    print("\n❌ Test 3: Cashout Ended Game")
    try:
        MinesGameService.cashout(game)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_verification():
    """Test provably fair verification"""
    print_section("5. Testing Provably Fair Verification")
    
    user = User.objects.get(username='mines_test_user')
    
    # Create and end game
    game = MinesGameService.create_game(user, Decimal('10.00'), 5)
    
    # Hit mine to end game
    mine_pos = game.mine_positions[0]
    MinesGameService.open_cell(game, mine_pos[0], mine_pos[1])
    
    print(f"\n🔍 Verifying game {game.id}")
    
    # Get verification data
    verification = MinesGameService.get_verification_data(game)
    
    print(f"  Server seed: {verification['server_seed'][:32]}...")
    print(f"  Server seed hash: {verification['server_seed_hash'][:32]}...")
    print(f"  Client seed: {verification['client_seed'][:32]}...")
    print(f"  Nonce: {verification['nonce']}")
    print(f"  Mine count: {verification['mine_count']}")
    print(f"  Mine positions: {verification['mine_positions']}")
    print(f"  Is valid: {verification['is_valid']}")
    
    assert verification['is_valid'] == True
    print("  ✓ Game verified as provably fair")
    
    # Test verification on active game
    print("\n❌ Test: Verify Active Game")
    game2 = MinesGameService.create_game(user, Decimal('10.00'), 5)
    
    try:
        MinesGameService.get_verification_data(game2)
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def cleanup():
    """Clean up test data"""
    print_section("6. Cleanup")
    
    # Delete test games
    deleted_count = MinesGame.objects.filter(
        user__username='mines_test_user'
    ).delete()[0]
    print(f"\n✓ Deleted {deleted_count} test games")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Mines Game Service Test Suite")
    print("=" * 60)
    
    try:
        test_create_game()
        test_calculate_multiplier()
        test_open_cell()
        test_cashout()
        test_verification()
        cleanup()
        
        print("\n" + "=" * 60)
        print("  ✓ All Tests Completed Successfully!")
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
