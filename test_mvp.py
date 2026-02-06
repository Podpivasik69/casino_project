"""
Test script for MVP functionality
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

def test_registration():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    response = requests.post(f'{BASE_URL}/api/auth/register/', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 201

def test_login():
    """Test user login"""
    print("\n=== Testing Login ===")
    session = requests.Session()
    response = session.post(f'{BASE_URL}/api/auth/login/', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return session if response.status_code == 200 else None

def test_profile(session):
    """Test getting user profile"""
    print("\n=== Testing Profile ===")
    response = session.get(f'{BASE_URL}/api/auth/profile/')
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Username: {data.get('username')}")
    print(f"Balance: {data.get('balance')}")
    return response.status_code == 200

def test_deposit(session):
    """Test demo deposit"""
    print("\n=== Testing Deposit ===")
    response = session.post(f'{BASE_URL}/api/wallet/deposit/')
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Amount: {data.get('amount')}")
    print(f"New Balance: {data.get('new_balance')}")
    return response.status_code == 200

def test_create_game(session):
    """Test creating Mines game"""
    print("\n=== Testing Create Game ===")
    response = session.post(f'{BASE_URL}/api/games/mines/create/', json={
        'bet_amount': 100,
        'mine_count': 5
    })
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Game ID: {data.get('game_id')}")
    print(f"New Balance: {data.get('new_balance')}")
    return data.get('game_id') if response.status_code == 201 else None

def test_open_cell(session, game_id):
    """Test opening a cell"""
    print("\n=== Testing Open Cell ===")
    response = session.post(f'{BASE_URL}/api/games/mines/{game_id}/open/', json={
        'cell_index': 0
    })
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Hit Mine: {data.get('hit_mine')}")
    print(f"Multiplier: {data.get('current_multiplier')}")
    return response.status_code == 200 and not data.get('hit_mine')

def test_cashout(session, game_id):
    """Test cashing out"""
    print("\n=== Testing Cashout ===")
    response = session.post(f'{BASE_URL}/api/games/mines/{game_id}/cashout/')
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Winnings: {data.get('winnings')}")
    print(f"New Balance: {data.get('new_balance')}")
    return response.status_code == 200

def test_transactions(session):
    """Test getting transactions"""
    print("\n=== Testing Transactions ===")
    response = session.get(f'{BASE_URL}/api/wallet/transactions/')
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Transaction Count: {len(data.get('transactions', []))}")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("=" * 50)
    print("SKET CASINO MVP TEST SUITE")
    print("=" * 50)
    
    # Test registration
    if not test_registration():
        print("\n❌ Registration failed")
        return
    
    # Test login
    session = test_login()
    if not session:
        print("\n❌ Login failed")
        return
    
    # Test profile
    if not test_profile(session):
        print("\n❌ Profile test failed")
        return
    
    # Test deposit
    if not test_deposit(session):
        print("\n❌ Deposit test failed")
        return
    
    # Test create game
    game_id = test_create_game(session)
    if not game_id:
        print("\n❌ Create game failed")
        return
    
    # Test open cell
    if not test_open_cell(session, game_id):
        print("\n❌ Open cell failed")
        return
    
    # Test cashout
    if not test_cashout(session, game_id):
        print("\n❌ Cashout failed")
        return
    
    # Test transactions
    if not test_transactions(session):
        print("\n❌ Transactions test failed")
        return
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("=" * 50)

if __name__ == '__main__':
    main()
