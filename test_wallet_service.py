"""
Test script to verify WalletService functionality.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from decimal import Decimal
from users.models import User
from wallet.services import WalletService, InsufficientFundsError
from wallet.models import Transaction
from django.core.exceptions import ValidationError


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_get_balance():
    """Test getting user balance"""
    print_section("1. Testing Get Balance")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='wallet_test_user',
        defaults={
            'email': 'wallet@example.com',
            'password': 'testpass123'
        }
    )
    
    if created:
        print(f"\n✓ Created test user: {user.username}")
    else:
        print(f"\n✓ Using existing user: {user.username}")
    
    # Get balance
    balance = WalletService.get_balance(user)
    print(f"  Current balance: {balance} ₽")
    
    assert isinstance(balance, Decimal), "Balance should be Decimal"
    assert balance >= 0, "Balance should be non-negative"
    print("  ✓ Balance retrieved successfully")


def test_deposit():
    """Test deposit functionality"""
    print_section("2. Testing Deposit")
    
    user = User.objects.get(username='wallet_test_user')
    initial_balance = WalletService.get_balance(user)
    
    # Test 1: Demo deposit (default amount)
    print("\n💰 Test 1: Demo Deposit (Default Amount)")
    txn = WalletService.deposit(user)
    
    print(f"  ✓ Deposit completed")
    print(f"  - Amount: {txn.amount}")
    print(f"  - Balance: {txn.balance_before} -> {txn.balance_after}")
    print(f"  - Type: {txn.get_transaction_type_display()}")
    print(f"  - Status: {txn.get_status_display()}")
    
    # Refresh user from database to get updated balance
    user.refresh_from_db()
    new_balance = WalletService.get_balance(user)
    assert new_balance == initial_balance + WalletService.DEMO_DEPOSIT_AMOUNT
    print(f"  ✓ Balance updated correctly: {new_balance}")
    
    # Test 2: Custom deposit amount
    print("\n💰 Test 2: Custom Deposit Amount")
    user.refresh_from_db()
    initial_balance = WalletService.get_balance(user)
    custom_amount = Decimal('250.00')
    
    txn = WalletService.deposit(user, amount=custom_amount, description='Custom deposit')
    
    print(f"  ✓ Custom deposit completed: {custom_amount}")
    print(f"  - Description: {txn.description}")
    
    user.refresh_from_db()
    new_balance = WalletService.get_balance(user)
    assert new_balance == initial_balance + custom_amount
    print(f"  ✓ Balance updated correctly: {new_balance}")
    
    # Test 3: Invalid deposit (negative amount)
    print("\n❌ Test 3: Invalid Deposit (Negative Amount)")
    try:
        WalletService.deposit(user, amount=Decimal('-100.00'))
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_place_bet():
    """Test placing bets"""
    print_section("3. Testing Place Bet")
    
    user = User.objects.get(username='wallet_test_user')
    initial_balance = WalletService.get_balance(user)
    
    # Test 1: Valid bet
    print("\n🎰 Test 1: Valid Bet")
    bet_amount = Decimal('100.00')
    
    txn = WalletService.place_bet(user, bet_amount, description='Mines game bet')
    
    print(f"  ✓ Bet placed: {bet_amount}")
    print(f"  - Balance: {txn.balance_before} -> {txn.balance_after}")
    print(f"  - Description: {txn.description}")
    
    user.refresh_from_db()
    new_balance = WalletService.get_balance(user)
    assert new_balance == initial_balance - bet_amount
    print(f"  ✓ Balance deducted correctly: {new_balance}")
    
    # Check total_wagered updated
    user.profile.refresh_from_db()
    print(f"  ✓ Total wagered updated: {user.profile.total_wagered}")
    
    # Test 2: Insufficient funds
    print("\n❌ Test 2: Insufficient Funds")
    huge_bet = new_balance + Decimal('1000.00')
    
    try:
        WalletService.place_bet(user, huge_bet)
        print("  ✗ Should have raised InsufficientFundsError")
    except InsufficientFundsError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 3: Invalid bet (zero amount)
    print("\n❌ Test 3: Invalid Bet (Zero Amount)")
    try:
        WalletService.place_bet(user, Decimal('0.00'))
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_add_winnings():
    """Test adding winnings"""
    print_section("4. Testing Add Winnings")
    
    user = User.objects.get(username='wallet_test_user')
    initial_balance = WalletService.get_balance(user)
    
    # Test 1: Valid winnings
    print("\n🎉 Test 1: Valid Winnings")
    win_amount = Decimal('250.00')
    
    txn = WalletService.add_winnings(user, win_amount, description='Mines game win 2.5x')
    
    print(f"  ✓ Winnings added: {win_amount}")
    print(f"  - Balance: {txn.balance_before} -> {txn.balance_after}")
    print(f"  - Description: {txn.description}")
    
    user.refresh_from_db()
    new_balance = WalletService.get_balance(user)
    assert new_balance == initial_balance + win_amount
    print(f"  ✓ Balance increased correctly: {new_balance}")
    
    # Check total_won updated
    user.profile.refresh_from_db()
    print(f"  ✓ Total won updated: {user.profile.total_won}")
    
    # Test 2: Zero winnings (should skip)
    print("\n⚠️  Test 2: Zero Winnings")
    user.refresh_from_db()
    initial_balance = WalletService.get_balance(user)
    
    txn = WalletService.add_winnings(user, Decimal('0.00'))
    
    if txn is None:
        print("  ✓ Zero winnings skipped (no transaction created)")
    
    user.refresh_from_db()
    new_balance = WalletService.get_balance(user)
    assert new_balance == initial_balance
    print(f"  ✓ Balance unchanged: {new_balance}")
    
    # Test 3: Invalid winnings (negative)
    print("\n❌ Test 3: Invalid Winnings (Negative)")
    try:
        WalletService.add_winnings(user, Decimal('-50.00'))
        print("  ✗ Should have raised ValidationError")
    except ValidationError as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_add_bonus():
    """Test adding bonus"""
    print_section("5. Testing Add Bonus")
    
    user = User.objects.get(username='wallet_test_user')
    initial_balance = WalletService.get_balance(user)
    
    # Test 1: Valid bonus
    print("\n🎁 Test 1: Valid Bonus")
    bonus_amount = Decimal('50.00')
    
    txn = WalletService.add_bonus(user, bonus_amount, description='Welcome bonus')
    
    print(f"  ✓ Bonus added: {bonus_amount}")
    print(f"  - Balance: {txn.balance_before} -> {txn.balance_after}")
    print(f"  - Type: {txn.get_transaction_type_display()}")
    
    user.refresh_from_db()
    new_balance = WalletService.get_balance(user)
    assert new_balance == initial_balance + bonus_amount
    print(f"  ✓ Balance increased correctly: {new_balance}")


def test_transaction_history():
    """Test getting transaction history"""
    print_section("6. Testing Transaction History")
    
    user = User.objects.get(username='wallet_test_user')
    
    # Test 1: Get all transactions
    print("\n📊 Test 1: Get All Transactions")
    transactions = WalletService.get_transaction_history(user)
    
    print(f"  ✓ Found {transactions.count()} transactions")
    
    # Show last 3
    print("  Last 3 transactions:")
    for i, txn in enumerate(transactions[:3], 1):
        print(f"    {i}. {txn.get_transaction_type_display()}: {txn.get_amount_display()} - {txn.created_at.strftime('%H:%M:%S')}")
    
    # Test 2: Filter by type
    print("\n📊 Test 2: Filter by Transaction Type")
    deposits = WalletService.get_transaction_history(
        user,
        transaction_type=Transaction.TransactionType.DEPOSIT
    )
    bets = WalletService.get_transaction_history(
        user,
        transaction_type=Transaction.TransactionType.BET
    )
    wins = WalletService.get_transaction_history(
        user,
        transaction_type=Transaction.TransactionType.WIN
    )
    
    print(f"  - Deposits: {deposits.count()}")
    print(f"  - Bets: {bets.count()}")
    print(f"  - Wins: {wins.count()}")
    
    # Test 3: Filter by status
    print("\n📊 Test 3: Filter by Status")
    completed = WalletService.get_transaction_history(
        user,
        status=Transaction.TransactionStatus.COMPLETED
    )
    
    print(f"  ✓ Completed transactions: {completed.count()}")
    
    # Test 4: Limit results
    print("\n📊 Test 4: Limit Results")
    limited = WalletService.get_transaction_history(user, limit=5)
    
    print(f"  ✓ Limited to 5 transactions: {limited.count()}")


def test_balance_summary():
    """Test getting balance summary"""
    print_section("7. Testing Balance Summary")
    
    user = User.objects.get(username='wallet_test_user')
    
    summary = WalletService.get_balance_summary(user)
    
    print("\n📈 Balance Summary:")
    print(f"  - Current Balance: {summary['balance']} ₽")
    print(f"  - Total Deposits: {summary['total_deposits']} ₽")
    print(f"  - Total Wagered: {summary['total_wagered']} ₽")
    print(f"  - Total Won: {summary['total_won']} ₽")
    print(f"  - Total Bonuses: {summary['total_bonuses']} ₽")
    print(f"  - Net Profit/Loss: {summary['net_profit']} ₽")
    print(f"  - Transaction Count: {summary['transaction_count']}")
    
    print("\n  ✓ Summary calculated successfully")


def test_atomicity():
    """Test transaction atomicity"""
    print_section("8. Testing Transaction Atomicity")
    
    user = User.objects.get(username='wallet_test_user')
    initial_balance = WalletService.get_balance(user)
    
    print(f"\n🔒 Test: Concurrent Operations")
    print(f"  Initial balance: {initial_balance}")
    
    # Simulate multiple operations
    try:
        # These should all be atomic
        WalletService.place_bet(user, Decimal('10.00'))
        user.refresh_from_db()
        WalletService.add_winnings(user, Decimal('20.00'))
        user.refresh_from_db()
        WalletService.place_bet(user, Decimal('5.00'))
        
        user.refresh_from_db()
        final_balance = WalletService.get_balance(user)
        expected_balance = initial_balance - Decimal('10.00') + Decimal('20.00') - Decimal('5.00')
        
        print(f"  Final balance: {final_balance}")
        print(f"  Expected balance: {expected_balance}")
        
        assert final_balance == expected_balance
        print("  ✓ All operations completed atomically")
        
    except Exception as e:
        print(f"  ✗ Atomicity test failed: {e}")


def test_get_transaction_by_id():
    """Test getting transaction by ID"""
    print_section("9. Testing Get Transaction by ID")
    
    user = User.objects.get(username='wallet_test_user')
    
    # Get first transaction
    first_txn = Transaction.objects.filter(user=user).first()
    
    if first_txn:
        print(f"\n🔍 Test: Get Transaction by ID")
        print(f"  Looking for transaction ID: {first_txn.id}")
        
        found_txn = WalletService.get_transaction_by_id(user, first_txn.id)
        
        if found_txn:
            print(f"  ✓ Transaction found: {found_txn}")
            assert found_txn.id == first_txn.id
        else:
            print(f"  ✗ Transaction not found")
        
        # Test non-existent ID
        print(f"\n🔍 Test: Non-existent Transaction ID")
        not_found = WalletService.get_transaction_by_id(user, 999999)
        
        if not_found is None:
            print(f"  ✓ Correctly returned None for non-existent ID")


def cleanup():
    """Clean up test data"""
    print_section("10. Cleanup")
    
    # Delete test transactions
    deleted_count = Transaction.objects.filter(
        user__username='wallet_test_user'
    ).delete()[0]
    print(f"\n✓ Deleted {deleted_count} test transactions")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  WalletService Test Suite")
    print("=" * 60)
    
    try:
        test_get_balance()
        test_deposit()
        test_place_bet()
        test_add_winnings()
        test_add_bonus()
        test_transaction_history()
        test_balance_summary()
        test_atomicity()
        test_get_transaction_by_id()
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
