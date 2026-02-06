"""
Test script for bug fixes
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

def test_full_flow():
    """Test complete user flow"""
    print("\n" + "="*60)
    print("TESTING BUG FIXES - FULL FLOW")
    print("="*60)
    
    session = requests.Session()
    
    # 1. Register
    print("\n1. Testing Registration...")
    import random
    username = f'bugtest{random.randint(1000, 9999)}'
    response = session.post(f'{BASE_URL}/api/auth/register/', json={
        'username': username,
        'email': f'{username}@example.com',
        'password': 'bugtest123'
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   ✅ Registered: {data['user']['username']}")
        print(f"   ✅ Balance: {data['user']['balance']} ₽")
    else:
        print(f"   ❌ Failed: {response.json()}")
        return False
    
    # 2. Login
    print("\n2. Testing Login...")
    response = session.post(f'{BASE_URL}/api/auth/login/', json={
        'username': username,
        'password': 'bugtest123'
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Logged in: {data['user']['username']}")
        print(f"   ✅ Balance: {data['user']['balance']} ₽")
    else:
        print(f"   ❌ Failed: {response.json()}")
        return False
    
    # 3. Deposit
    print("\n3. Testing Demo Deposit...")
    response = session.post(f'{BASE_URL}/api/wallet/deposit/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Deposited: {data['amount']} ₽")
        print(f"   ✅ New Balance: {data['new_balance']} ₽")
    else:
        print(f"   ❌ Failed: {response.json()}")
        return False
    
    # 4. Create Mines Game
    print("\n4. Testing Create Mines Game...")
    response = session.post(f'{BASE_URL}/api/games/mines/create/', json={
        'bet_amount': 100,
        'mine_count': 5
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        game_id = data['game_id']
        print(f"   ✅ Game Created: ID={game_id}")
        print(f"   ✅ Bet Amount: {data['bet_amount']} ₽")
        print(f"   ✅ Mine Count: {data['mine_count']}")
        print(f"   ✅ New Balance: {data.get('new_balance', 'N/A')} ₽")
    else:
        print(f"   ❌ Failed: {response.json()}")
        return False
    
    # 5. Open Cell
    print("\n5. Testing Open Cell...")
    response = session.post(f'{BASE_URL}/api/games/mines/{game_id}/open/', json={
        'cell_index': 0
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data['hit_mine']:
            print(f"   💣 Hit Mine!")
            print(f"   ✅ Mine Positions: {data['mine_positions']}")
        else:
            print(f"   💎 Safe Cell!")
            print(f"   ✅ Multiplier: {data['current_multiplier']}x")
            print(f"   ✅ Opened Count: {data['opened_count']}")
            
            # Try to open more cells
            for cell_idx in [1, 2, 3]:
                response = session.post(f'{BASE_URL}/api/games/mines/{game_id}/open/', json={
                    'cell_index': cell_idx
                })
                if response.status_code == 200:
                    data = response.json()
                    if data['hit_mine']:
                        print(f"   💣 Hit Mine at cell {cell_idx}!")
                        break
                    else:
                        print(f"   💎 Cell {cell_idx} safe! Multiplier: {data['current_multiplier']}x")
            
            # 6. Cashout (if not hit mine)
            if not data.get('hit_mine'):
                print("\n6. Testing Cashout...")
                response = session.post(f'{BASE_URL}/api/games/mines/{game_id}/cashout/')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Cashed Out!")
                    print(f"   ✅ Winnings: {data['winnings']} ₽")
                    print(f"   ✅ Multiplier: {data['multiplier']}x")
                    print(f"   ✅ New Balance: {data.get('new_balance', 'N/A')} ₽")
                else:
                    print(f"   ❌ Failed: {response.json()}")
    else:
        print(f"   ❌ Failed: {response.json()}")
        return False
    
    # 7. Logout
    print("\n7. Testing Logout...")
    response = session.post(f'{BASE_URL}/api/auth/logout/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Logged Out: {data['message']}")
    else:
        print(f"   ❌ Failed: {response.json()}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    return True

if __name__ == '__main__':
    test_full_flow()
