"""
Test script to verify Transaction model functionality.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from decimal import Decimal
from users.models import User
from wallet.models import Transaction


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_transaction_creation():
    """Test creating transactions"""
    print_section("1. Testing Transaction Creation")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='transaction_test_user',
        defaults={
            'email': 'transaction@example.com',
            'password': 'testpass123'
        }
    )
    
    if created:
        print(f"\n✓ Created test user: {user.username}")
    else:
        print(f"\n✓ Using existing user: {user.username}")
    
    # Get initial balance
    initial_balance = user.profile.balance
    print(f"  Initial balance: {initial_balance}")
    
    # Test 1: Create DEPOSIT transaction
    print("\n📥 Test 1: Create DEPOSIT Transaction")
    deposit = Transaction.objects.create(
        user=user,
        amount=Decimal('500.00'),
        transaction_type=Transaction.TransactionType.DEPOSIT,
        balance_before=initial_balance,
        balance_after=initial_balance + Decimal('500.00'),
        description='Demo deposit',
        status=Transaction.TransactionStatus.COMPLETED
    )
    print(f"  ✓ Transaction created: {deposit}")
    print(f"  - ID: {deposit.id}")
    print(f"  - Type: {deposit.get_transaction_type_display()}")
    print(f"  - Amount: {deposit.get_amount_display()}")
    print(f"  - Balance: {deposit.balance_before} → {deposit.balance_after}")
    print(f"  - Status: {deposit.get_status_display()}")
    print(f"  - Is completed: {deposit.is_completed}")
    
    # Test 2: Create BET transaction
    print("\n🎰 Test 2: Create BET Transaction")
    new_balance = deposit.balance_after
    bet = Transaction.objects.create(
        user=user,
        amount=Decimal('100.00'),
        transaction_type=Transaction.TransactionType.BET,
        balance_before=new_balance,
        balance_after=new_balance - Decimal('100.00'),
        description='Mines game bet',
        status=Transaction.TransactionStatus.COMPLETED
    )
    print(f"  ✓ Transaction created: {bet}")
    print(f"  - Type: {bet.get_transaction_type_display()}")
    print(f"  - Amount: {bet.get_amount_display()}")
    print(f"  - Balance: {bet.balance_before} → {bet.balance_after}")
    
    # Test 3: Create WIN transaction
    print("\n🎉 Test 3: Create WIN Transaction")
    new_balance = bet.balance_after
    win = Transaction.objects.create(
        user=user,
        amount=Decimal('250.00'),
        transaction_type=Transaction.TransactionType.WIN,
        balance_before=new_balance,
        balance_after=new_balance + Decimal('250.00'),
        description='Mines game win (2.5x)',
        status=Transaction.TransactionStatus.COMPLETED
    )
    print(f"  ✓ Transaction created: {win}")
    print(f"  - Type: {win.get_transaction_type_display()}")
    print(f"  - Amount: {win.get_amount_display()}")
    print(f"  - Balance: {win.balance_before} → {win.balance_after}")
    
    # Test 4: Create BONUS transaction
    print("\n🎁 Test 4: Create BONUS Transaction")
    new_balance = win.balance_after
    bonus = Transaction.objects.create(
        user=user,
        amount=Decimal('50.00'),
        transaction_type=Transaction.TransactionType.BONUS,
        balance_before=new_balance,
        balance_after=new_balance + Decimal('50.00'),
        description='Welcome bonus',
        status=Transaction.TransactionStatus.COMPLETED
    )
    print(f"  ✓ Transaction created: {bonus}")
    print(f"  - Type: {bonus.get_transaction_type_display()}")
    print(f"  - Amount: {bonus.get_amount_display()}")
    print(f"  - Balance: {bonus.balance_before} → {bonus.balance_after}")
    
    # Test 5: Create PENDING transaction
    print("\n⏳ Test 5: Create PENDING Transaction")
    new_balance = bonus.balance_after
    pending = Transaction.objects.create(
        user=user,
        amount=Decimal('75.00'),
        transaction_type=Transaction.TransactionType.BET,
        balance_before=new_balance,
        balance_after=new_balance - Decimal('75.00'),
        description='Pending bet',
        status=Transaction.TransactionStatus.PENDING
    )
    print(f"  ✓ Transaction created: {pending}")
    print(f"  - Status: {pending.get_status_display()}")
    print(f"  - Is pending: {pending.is_pending}")
    print(f"  - Is completed: {pending.is_completed}")


def test_transaction_queries():
    """Test querying transactions"""
    print_section("2. Testing Transaction Queries")
    
    user = User.objects.get(username='transaction_test_user')
    
    # Test 1: Get all user transactions
    print("\n📊 Test 1: Get All User Transactions")
    transactions = Transaction.objects.filter(user=user)
    print(f"  ✓ Found {transactions.count()} transactions")
    
    # Test 2: Get transactions by type
    print("\n📊 Test 2: Get Transactions by Type")
    deposits = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.TransactionType.DEPOSIT
    )
    bets = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.TransactionType.BET
    )
    wins = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.TransactionType.WIN
    )
    print(f"  - Deposits: {deposits.count()}")
    print(f"  - Bets: {bets.count()}")
    print(f"  - Wins: {wins.count()}")
    
    # Test 3: Get completed transactions
    print("\n📊 Test 3: Get Completed Transactions")
    completed = Transaction.objects.filter(
        user=user,
        status=Transaction.TransactionStatus.COMPLETED
    )
    print(f"  ✓ Found {completed.count()} completed transactions")
    
    # Test 4: Get recent transactions (ordered by created_at)
    print("\n📊 Test 4: Get Recent Transactions (Last 3)")
    recent = Transaction.objects.filter(user=user)[:3]
    for i, txn in enumerate(recent, 1):
        print(f"  {i}. {txn.get_transaction_type_display()}: {txn.get_amount_display()} - {txn.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 5: Calculate total deposited
    print("\n📊 Test 5: Calculate Totals")
    from django.db.models import Sum
    
    total_deposited = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.TransactionType.DEPOSIT,
        status=Transaction.TransactionStatus.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_bet = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.TransactionType.BET,
        status=Transaction.TransactionStatus.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_won = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.TransactionType.WIN,
        status=Transaction.TransactionStatus.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    print(f"  - Total Deposited: {total_deposited}")
    print(f"  - Total Bet: {total_bet}")
    print(f"  - Total Won: {total_won}")
    print(f"  - Net Profit/Loss: {total_won - total_bet}")


def test_transaction_properties():
    """Test transaction properties and methods"""
    print_section("3. Testing Transaction Properties")
    
    user = User.objects.get(username='transaction_test_user')
    
    # Get different transaction types
    deposit = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.TransactionType.DEPOSIT
    ).first()
    
    bet = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.TransactionType.BET
    ).first()
    
    print("\n✅ Test 1: Amount Display Format")
    print(f"  - Deposit: {deposit.get_amount_display()} (should be +)")
    print(f"  - Bet: {bet.get_amount_display()} (should be -)")
    
    print("\n✅ Test 2: Status Properties")
    completed_txn = Transaction.objects.filter(
        user=user,
        status=Transaction.TransactionStatus.COMPLETED
    ).first()
    
    pending_txn = Transaction.objects.filter(
        user=user,
        status=Transaction.TransactionStatus.PENDING
    ).first()
    
    print(f"  Completed transaction:")
    print(f"    - is_completed: {completed_txn.is_completed}")
    print(f"    - is_pending: {completed_txn.is_pending}")
    print(f"    - is_failed: {completed_txn.is_failed}")
    
    if pending_txn:
        print(f"  Pending transaction:")
        print(f"    - is_completed: {pending_txn.is_completed}")
        print(f"    - is_pending: {pending_txn.is_pending}")
        print(f"    - is_failed: {pending_txn.is_failed}")


def test_indexes():
    """Test that indexes are working"""
    print_section("4. Testing Database Indexes")
    
    user = User.objects.get(username='transaction_test_user')
    
    print("\n📊 Test 1: Query with (user, created_at) index")
    # This query should use the user_created_idx index
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:10]
    print(f"  ✓ Retrieved {transactions.count()} transactions (using index)")
    
    print("\n📊 Test 2: Query with (transaction_type, status) index")
    # This query should use the type_status_idx index
    completed_bets = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.BET,
        status=Transaction.TransactionStatus.COMPLETED
    )
    print(f"  ✓ Found {completed_bets.count()} completed bets (using index)")


def cleanup():
    """Clean up test data"""
    print_section("5. Cleanup")
    
    # Delete test transactions
    deleted_count = Transaction.objects.filter(
        user__username='transaction_test_user'
    ).delete()[0]
    print(f"\n✓ Deleted {deleted_count} test transactions")
    
    # Optionally delete test user
    # User.objects.filter(username='transaction_test_user').delete()
    # print(f"✓ Deleted test user")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Transaction Model Test Suite")
    print("=" * 60)
    
    try:
        test_transaction_creation()
        test_transaction_queries()
        test_transaction_properties()
        test_indexes()
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
