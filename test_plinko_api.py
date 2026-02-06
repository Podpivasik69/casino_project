"""
Test script for Plinko Game API endpoints.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

import json
from decimal import Decimal
from django.test import Client
from users.models import User
from wallet.services import WalletService


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_create_game_api():
    """Test create game API endpoint"""
    print_section("1. Testing Create Game API")
    
    # Setup
    client = Client()
    user, created = User.objects.get_or_create(
        username='plinko_api_test',
        defaults={'email': 'plinko_api@example.com'}
    )
    user.set_password('testpass123')
    user.save()
    
    # Ensure balance
    balance = WalletService.get_balance(user)
    if balance < Decimal('100.00'):
        WalletService.deposit(user, Decimal('1000.00'))
    
    # Login
    client.login(username='plinko_api_test', password='testpass123')
    
    # Test 1: Create valid game
    print("\n✓ Test 1: Create Valid Game")
    response = client.post(
        '/api/games/plinko/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'row_count': 14,
            'risk_level': 'medium'
        }),
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    data = response.json()
    print(f"  - Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'game' in data
    game_id = data['game']['id']
    print(f"  ✓ Game created: ID={game_id}")
    
    # Test 2: Invalid row count
    print("\n❌ Test 2: Invalid Row Count")
    response = client.post(
        '/api/games/plinko/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'row_count': 11,
            'risk_level': 'medium'
        }),
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    data = response.json()
    print(f"  - Error: {data.get('error')}")
    assert response.status_code == 400
    assert data['success'] is False
    print("  ✓ Correctly rejected")
    
    # Test 3: Invalid risk level
    print("\n❌ Test 3: Invalid Risk Level")
    response = client.post(
        '/api/games/plinko/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'row_count': 14,
            'risk_level': 'invalid'
        }),
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    data = response.json()
    print(f"  - Error: {data.get('error')}")
    assert response.status_code == 400
    print("  ✓ Correctly rejected")


def test_drop_ball_api():
    """Test drop ball API endpoint"""
    print_section("2. Testing Drop Ball API")
    
    client = Client()
    user = User.objects.get(username='plinko_api_test')
    client.login(username='plinko_api_test', password='testpass123')
    
    # Ensure balance
    balance = WalletService.get_balance(user)
    if balance < Decimal('100.00'):
        WalletService.deposit(user, Decimal('1000.00'))
    
    # Create game
    response = client.post(
        '/api/games/plinko/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'row_count': 14,
            'risk_level': 'medium'
        }),
        content_type='application/json'
    )
    game_id = response.json()['game']['id']
    
    # Test 1: Drop ball successfully
    print("\n✓ Test 1: Drop Ball Successfully")
    response = client.post(
        f'/api/games/plinko/{game_id}/drop/',
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    data = response.json()
    print(f"  - Ball path: {data['result']['ball_path']}")
    print(f"  - Bucket: {data['result']['bucket_index']}")
    print(f"  - Multiplier: {data['result']['multiplier']}x")
    print(f"  - Winnings: {data['result']['winnings']} ₽")
    print(f"  - New balance: {data['balance']} ₽")
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'result' in data
    print("  ✓ Ball dropped successfully")
    
    # Test 2: Cannot drop twice
    print("\n❌ Test 2: Cannot Drop Ball Twice")
    response = client.post(
        f'/api/games/plinko/{game_id}/drop/',
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    data = response.json()
    print(f"  - Error: {data.get('error')}")
    assert response.status_code == 400
    print("  ✓ Correctly rejected")
    
    # Test 3: Invalid game ID
    print("\n❌ Test 3: Invalid Game ID")
    response = client.post(
        '/api/games/plinko/99999/drop/',
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    assert response.status_code == 404
    print("  ✓ Correctly rejected")


def test_get_game_api():
    """Test get game API endpoint"""
    print_section("3. Testing Get Game API")
    
    client = Client()
    user = User.objects.get(username='plinko_api_test')
    client.login(username='plinko_api_test', password='testpass123')
    
    # Ensure balance
    balance = WalletService.get_balance(user)
    if balance < Decimal('100.00'):
        WalletService.deposit(user, Decimal('1000.00'))
    
    # Create and complete game
    response = client.post(
        '/api/games/plinko/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'row_count': 14,
            'risk_level': 'high'
        }),
        content_type='application/json'
    )
    game_id = response.json()['game']['id']
    
    client.post(f'/api/games/plinko/{game_id}/drop/', content_type='application/json')
    
    # Test 1: Get game details
    print("\n✓ Test 1: Get Game Details")
    response = client.get(f'/api/games/plinko/{game_id}/')
    
    print(f"  - Status: {response.status_code}")
    data = response.json()
    print(f"  - Game ID: {data['game']['id']}")
    print(f"  - Bet: {data['game']['bet_amount']} ₽")
    print(f"  - Rows: {data['game']['row_count']}")
    print(f"  - Risk: {data['game']['risk_level_display']}")
    print(f"  - Completed: {data['game']['is_completed']}")
    print(f"  - Multiplier: {data['game']['final_multiplier']}x")
    
    assert response.status_code == 200
    assert data['success'] is True
    assert data['game']['is_completed'] is True
    print("  ✓ Game details retrieved")
    
    # Test 2: Invalid game ID
    print("\n❌ Test 2: Invalid Game ID")
    response = client.get('/api/games/plinko/99999/')
    
    print(f"  - Status: {response.status_code}")
    assert response.status_code == 404
    print("  ✓ Correctly rejected")


def test_auto_play_api():
    """Test auto-play API endpoint"""
    print_section("4. Testing Auto-Play API")
    
    client = Client()
    user = User.objects.get(username='plinko_api_test')
    client.login(username='plinko_api_test', password='testpass123')
    
    # Ensure balance
    balance = WalletService.get_balance(user)
    if balance < Decimal('500.00'):
        WalletService.deposit(user, Decimal('1000.00'))
    
    # Test 1: Auto-play 5 drops
    print("\n✓ Test 1: Auto-Play 5 Drops")
    initial_balance = WalletService.get_balance(user)
    print(f"  - Initial balance: {initial_balance} ₽")
    
    response = client.post(
        '/api/games/plinko/auto/',
        data=json.dumps({
            'bet_amount': '10.00',
            'row_count': 14,
            'risk_level': 'medium',
            'drop_count': 5
        }),
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    data = response.json()
    print(f"  - Total drops: {data['total_drops']}")
    print(f"  - Total winnings: {data['total_winnings']} ₽")
    print(f"  - Final balance: {data['balance']} ₽")
    
    for i, result in enumerate(data['results'], 1):
        print(f"    Drop {i}: Bucket {result['bucket_index']}, {result['multiplier']}x, {result['winnings']} ₽")
    
    assert response.status_code == 200
    assert data['success'] is True
    assert data['total_drops'] == 5
    print("  ✓ Auto-play completed")
    
    # Test 2: Invalid drop count
    print("\n❌ Test 2: Invalid Drop Count")
    response = client.post(
        '/api/games/plinko/auto/',
        data=json.dumps({
            'bet_amount': '10.00',
            'row_count': 14,
            'risk_level': 'medium',
            'drop_count': 0
        }),
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    assert response.status_code == 400
    print("  ✓ Correctly rejected")


def test_get_multipliers_api():
    """Test get multipliers API endpoint"""
    print_section("5. Testing Get Multipliers API")
    
    client = Client()
    user = User.objects.get(username='plinko_api_test')
    client.login(username='plinko_api_test', password='testpass123')
    
    # Test 1: Get all multipliers
    print("\n✓ Test 1: Get All Multipliers")
    response = client.get('/api/games/plinko/multipliers/')
    
    print(f"  - Status: {response.status_code}")
    data = response.json()
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'multipliers' in data
    
    for risk in ['low', 'medium', 'high']:
        print(f"\n  {risk.upper()} Risk:")
        for rows in [12, 13, 14, 15, 16]:
            mults = data['multipliers'][risk][str(rows)]
            print(f"    {rows} rows: {len(mults)} buckets, max {max(mults)}x")
    
    print("\n  ✓ Multipliers retrieved")


def test_authentication():
    """Test authentication requirements"""
    print_section("6. Testing Authentication")
    
    client = Client()
    
    # Test 1: Unauthenticated create game
    print("\n❌ Test 1: Unauthenticated Create Game")
    response = client.post(
        '/api/games/plinko/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'row_count': 14,
            'risk_level': 'medium'
        }),
        content_type='application/json'
    )
    
    print(f"  - Status: {response.status_code}")
    assert response.status_code == 302  # Redirect to login
    print("  ✓ Correctly requires authentication")


def run_all_tests():
    """Run all API tests"""
    print("\n" + "=" * 60)
    print("  PLINKO GAME API - TEST SUITE")
    print("=" * 60)
    
    try:
        test_create_game_api()
        test_drop_ball_api()
        test_get_game_api()
        test_auto_play_api()
        test_get_multipliers_api()
        test_authentication()
        
        print("\n" + "=" * 60)
        print("  ✓ ALL API TESTS PASSED")
        print("=" * 60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        raise


if __name__ == '__main__':
    run_all_tests()
