"""
Test script for Wallet API endpoints.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from django.test import Client
from users.models import User
import json


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_response(response):
    """Print response details"""
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"  Response: {response.content.decode()}")


def test_get_balance():
    """Test GET /api/wallet/balance/"""
    print_section("1. Testing GET /api/wallet/balance/")
    
    client = Client()
    
    # Create and login user
    user = User.objects.get(username='wallet_test_user')
    client.force_login(user)
    
    # Test 1: Get balance
    print("\n💰 Test 1: Get Balance (Authenticated)")
    response = client.get('/api/wallet/balance/')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert 'balance' in data
    assert 'currency' in data
    print("  ✓ Balance retrieved successfully")
    
    # Test 2: Unauthenticated request
    print("\n❌ Test 2: Get Balance (Unauthenticated)")
    client.logout()
    response = client.get('/api/wallet/balance/')
    print_response(response)
    
    assert response.status_code == 302  # Redirect to login
    print("  ✓ Correctly requires authentication")


def test_demo_deposit():
    """Test POST /api/wallet/deposit/"""
    print_section("2. Testing POST /api/wallet/deposit/")
    
    client = Client()
    
    # Login user
    user = User.objects.get(username='wallet_test_user')
    client.force_login(user)
    
    # Get initial balance
    response = client.get('/api/wallet/balance/')
    initial_balance = float(response.json()['balance'])
    
    # Test 1: Demo deposit
    print("\n💰 Test 1: Demo Deposit (500 RUB)")
    response = client.post('/api/wallet/deposit/')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert data['amount'] == '500.00'
    assert 'transaction_id' in data
    print("  ✓ Demo deposit completed")
    
    # Verify balance increased
    response = client.get('/api/wallet/balance/')
    new_balance = float(response.json()['balance'])
    assert new_balance == initial_balance + 500.00
    print(f"  ✓ Balance increased: {initial_balance} -> {new_balance}")
    
    # Test 2: Unauthenticated request
    print("\n❌ Test 2: Demo Deposit (Unauthenticated)")
    client.logout()
    response = client.post('/api/wallet/deposit/')
    print_response(response)
    
    assert response.status_code == 302  # Redirect to login
    print("  ✓ Correctly requires authentication")


def test_get_transactions():
    """Test GET /api/wallet/transactions/"""
    print_section("3. Testing GET /api/wallet/transactions/")
    
    client = Client()
    
    # Login user
    user = User.objects.get(username='wallet_test_user')
    client.force_login(user)
    
    # Test 1: Get all transactions
    print("\n📊 Test 1: Get All Transactions")
    response = client.get('/api/wallet/transactions/')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert 'transactions' in data
    assert 'count' in data
    print(f"  ✓ Retrieved {data['count']} transactions")
    
    # Test 2: Filter by type
    print("\n📊 Test 2: Filter by Type (deposit)")
    response = client.get('/api/wallet/transactions/?type=deposit')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    print(f"  ✓ Retrieved {data['count']} deposit transactions")
    
    # Test 3: Limit results
    print("\n📊 Test 3: Limit Results (5)")
    response = client.get('/api/wallet/transactions/?limit=5')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data['count'] <= 5
    print(f"  ✓ Limited to {data['count']} transactions")
    
    # Test 4: Invalid limit
    print("\n❌ Test 4: Invalid Limit (200)")
    response = client.get('/api/wallet/transactions/?limit=200')
    print_response(response)
    
    assert response.status_code == 400
    print("  ✓ Correctly rejected invalid limit")


def test_get_balance_summary():
    """Test GET /api/wallet/summary/"""
    print_section("4. Testing GET /api/wallet/summary/")
    
    client = Client()
    
    # Login user
    user = User.objects.get(username='wallet_test_user')
    client.force_login(user)
    
    # Test 1: Get balance summary
    print("\n📈 Test 1: Get Balance Summary")
    response = client.get('/api/wallet/summary/')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all required fields
    required_fields = [
        'balance', 'total_wagered', 'total_won',
        'total_deposits', 'total_bonuses', 'net_profit',
        'transaction_count'
    ]
    
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    print("  ✓ All fields present in summary")
    print(f"  - Balance: {data['balance']} ₽")
    print(f"  - Total Deposits: {data['total_deposits']} ₽")
    print(f"  - Net Profit: {data['net_profit']} ₽")
    print(f"  - Transactions: {data['transaction_count']}")


def test_complete_workflow():
    """Test complete wallet workflow"""
    print_section("5. Testing Complete Workflow")
    
    client = Client()
    
    # Create new test user
    user, created = User.objects.get_or_create(
        username='workflow_test_user',
        defaults={
            'email': 'workflow@example.com',
            'password': 'testpass123'
        }
    )
    
    if created:
        print("\n✓ Created new test user")
    
    client.force_login(user)
    
    # Step 1: Check initial balance
    print("\n📊 Step 1: Check Initial Balance")
    response = client.get('/api/wallet/balance/')
    initial_balance = float(response.json()['balance'])
    print(f"  Initial balance: {initial_balance} ₽")
    
    # Step 2: Make demo deposit
    print("\n💰 Step 2: Make Demo Deposit")
    response = client.post('/api/wallet/deposit/')
    print(f"  Deposited: {response.json()['amount']} ₽")
    
    # Step 3: Check updated balance
    print("\n📊 Step 3: Check Updated Balance")
    response = client.get('/api/wallet/balance/')
    new_balance = float(response.json()['balance'])
    print(f"  New balance: {new_balance} ₽")
    assert new_balance == initial_balance + 500.00
    
    # Step 4: Check transaction history
    print("\n📊 Step 4: Check Transaction History")
    response = client.get('/api/wallet/transactions/?limit=5')
    transactions = response.json()['transactions']
    print(f"  Recent transactions: {len(transactions)}")
    
    if transactions:
        last_txn = transactions[0]
        print(f"  Last transaction: {last_txn['type_display']} {last_txn['amount']} ₽")
    
    # Step 5: Get balance summary
    print("\n📈 Step 5: Get Balance Summary")
    response = client.get('/api/wallet/summary/')
    summary = response.json()
    print(f"  Total deposits: {summary['total_deposits']} ₽")
    print(f"  Transaction count: {summary['transaction_count']}")
    
    print("\n  ✓ Complete workflow executed successfully")
    
    # Cleanup
    if created:
        from wallet.models import Transaction
        Transaction.objects.filter(user=user).delete()
        user.delete()
        print("  ✓ Test user cleaned up")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Wallet API Test Suite")
    print("=" * 60)
    
    try:
        # Ensure test user exists
        user, created = User.objects.get_or_create(
            username='wallet_test_user',
            defaults={
                'email': 'wallet@example.com',
                'password': 'testpass123'
            }
        )
        
        if created:
            print("\n✓ Created test user: wallet_test_user")
        
        test_get_balance()
        test_demo_deposit()
        test_get_transactions()
        test_get_balance_summary()
        test_complete_workflow()
        
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
