"""
Test script for Mines Game API endpoints.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from django.test import Client
from users.models import User
from games.models import MinesGame
from wallet.services import WalletService
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


def test_create_game():
    """Test POST /api/games/mines/create/"""
    print_section("1. Testing POST /api/games/mines/create/")
    
    client = Client()
    
    # Create and login user
    user, created = User.objects.get_or_create(
        username='mines_api_test_user',
        defaults={
            'email': 'minesapi@example.com',
            'password': 'testpass123'
        }
    )
    
    if created:
        print(f"\n✓ Created test user: {user.username}")
    
    # Ensure user has balance
    balance = WalletService.get_balance(user)
    if balance < 100:
        WalletService.deposit(user, 1000)
        print(f"  ✓ Added demo balance: 1000.00")
    
    client.force_login(user)
    
    # Test 1: Create valid game
    print("\n🎮 Test 1: Create Valid Game")
    response = client.post(
        '/api/games/mines/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'mine_count': 5
        }),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'game_id' in data
    assert data['mine_count'] == 5
    print("  ✓ Game created successfully")
    
    game_id = data['game_id']
    
    # Test 2: Invalid mine count
    print("\n❌ Test 2: Invalid Mine Count")
    response = client.post(
        '/api/games/mines/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'mine_count': 2
        }),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 400
    print("  ✓ Correctly rejected invalid mine count")
    
    # Test 3: Insufficient funds
    print("\n❌ Test 3: Insufficient Funds")
    response = client.post(
        '/api/games/mines/create/',
        data=json.dumps({
            'bet_amount': '999999.00',
            'mine_count': 5
        }),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 400
    print("  ✓ Correctly rejected insufficient funds")
    
    return game_id


def test_get_game(game_id):
    """Test GET /api/games/mines/<id>/"""
    print_section("2. Testing GET /api/games/mines/<id>/")
    
    client = Client()
    user = User.objects.get(username='mines_api_test_user')
    client.force_login(user)
    
    # Test 1: Get existing game
    print(f"\n📊 Test 1: Get Game {game_id}")
    response = client.get(f'/api/games/mines/{game_id}/')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data['game_id'] == game_id
    assert 'state' in data
    assert 'current_multiplier' in data
    print("  ✓ Game retrieved successfully")
    
    # Test 2: Get non-existent game
    print("\n❌ Test 2: Get Non-existent Game")
    response = client.get('/api/games/mines/999999/')
    print_response(response)
    
    assert response.status_code == 404
    print("  ✓ Correctly returned 404")


def test_open_cell(game_id):
    """Test POST /api/games/mines/<id>/open/"""
    print_section("3. Testing POST /api/games/mines/<id>/open/")
    
    client = Client()
    user = User.objects.get(username='mines_api_test_user')
    client.force_login(user)
    
    # Get game to find safe cell
    game = MinesGame.objects.get(id=game_id)
    
    # Find safe cell
    safe_cell = None
    for row in range(5):
        for col in range(5):
            if [row, col] not in game.mine_positions:
                safe_cell = (row, col)
                break
        if safe_cell:
            break
    
    # Test 1: Open safe cell
    print(f"\n✅ Test 1: Open Safe Cell ({safe_cell[0]}, {safe_cell[1]})")
    response = client.post(
        f'/api/games/mines/{game_id}/open/',
        data=json.dumps({
            'row': safe_cell[0],
            'col': safe_cell[1]
        }),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data['is_mine'] == False
    assert data['success'] == True
    assert float(data['multiplier']) > 1.0
    print("  ✓ Safe cell opened successfully")
    
    # Test 2: Open already opened cell
    print(f"\n❌ Test 2: Open Already Opened Cell")
    response = client.post(
        f'/api/games/mines/{game_id}/open/',
        data=json.dumps({
            'row': safe_cell[0],
            'col': safe_cell[1]
        }),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 400
    print("  ✓ Correctly rejected already opened cell")
    
    # Test 3: Invalid coordinates
    print("\n❌ Test 3: Invalid Coordinates")
    response = client.post(
        f'/api/games/mines/{game_id}/open/',
        data=json.dumps({
            'row': 10,
            'col': 10
        }),
        content_type='application/json'
    )
    print_response(response)
    
    assert response.status_code == 400
    print("  ✓ Correctly rejected invalid coordinates")


def test_cashout(game_id):
    """Test POST /api/games/mines/<id>/cashout/"""
    print_section("4. Testing POST /api/games/mines/<id>/cashout/")
    
    client = Client()
    user = User.objects.get(username='mines_api_test_user')
    client.force_login(user)
    
    # Test 1: Valid cashout
    print(f"\n💰 Test 1: Cashout Game {game_id}")
    response = client.post(f'/api/games/mines/{game_id}/cashout/')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'winnings' in data
    assert data['game_state'] == 'cashed_out'
    assert 'verification' in data
    print("  ✓ Game cashed out successfully")
    
    # Test 2: Cashout already ended game
    print("\n❌ Test 2: Cashout Already Ended Game")
    response = client.post(f'/api/games/mines/{game_id}/cashout/')
    print_response(response)
    
    assert response.status_code == 400
    print("  ✓ Correctly rejected cashout of ended game")


def test_verify_game(game_id):
    """Test GET /api/games/mines/<id>/verify/"""
    print_section("5. Testing GET /api/games/mines/<id>/verify/")
    
    client = Client()
    user = User.objects.get(username='mines_api_test_user')
    client.force_login(user)
    
    # Test 1: Verify ended game
    print(f"\n🔍 Test 1: Verify Game {game_id}")
    response = client.get(f'/api/games/mines/{game_id}/verify/')
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert 'server_seed' in data
    assert 'mine_positions' in data
    assert data['is_valid'] == True
    print("  ✓ Game verified successfully")


def test_complete_workflow():
    """Test complete game workflow"""
    print_section("6. Testing Complete Workflow")
    
    client = Client()
    user = User.objects.get(username='mines_api_test_user')
    client.force_login(user)
    
    print("\n🎮 Complete Mines Game Workflow:")
    
    # Step 1: Create game
    print("\n  Step 1: Create Game")
    response = client.post(
        '/api/games/mines/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'mine_count': 5
        }),
        content_type='application/json'
    )
    game_id = response.json()['game_id']
    print(f"    ✓ Game created: ID={game_id}")
    
    # Step 2: Get game details
    print("\n  Step 2: Get Game Details")
    response = client.get(f'/api/games/mines/{game_id}/')
    data = response.json()
    print(f"    ✓ State: {data['state']}")
    print(f"    ✓ Multiplier: {data['current_multiplier']}x")
    
    # Step 3: Open 3 safe cells
    print("\n  Step 3: Open Safe Cells")
    game = MinesGame.objects.get(id=game_id)
    opened = 0
    
    for row in range(5):
        for col in range(5):
            if [row, col] not in game.mine_positions and opened < 3:
                response = client.post(
                    f'/api/games/mines/{game_id}/open/',
                    data=json.dumps({'row': row, 'col': col}),
                    content_type='application/json'
                )
                data = response.json()
                print(f"    ✓ Opened ({row}, {col}): multiplier={data['multiplier']}x")
                opened += 1
    
    # Step 4: Cashout
    print("\n  Step 4: Cashout")
    response = client.post(f'/api/games/mines/{game_id}/cashout/')
    data = response.json()
    print(f"    ✓ Winnings: {data['winnings']} ₽")
    print(f"    ✓ Multiplier: {data['multiplier']}x")
    
    # Step 5: Verify
    print("\n  Step 5: Verify Game")
    response = client.get(f'/api/games/mines/{game_id}/verify/')
    data = response.json()
    print(f"    ✓ Is valid: {data['is_valid']}")
    print(f"    ✓ Mine count: {data['mine_count']}")
    
    print("\n  ✓ Complete workflow executed successfully")


def test_mine_hit_workflow():
    """Test workflow when hitting a mine"""
    print_section("7. Testing Mine Hit Workflow")
    
    client = Client()
    user = User.objects.get(username='mines_api_test_user')
    client.force_login(user)
    
    print("\n💣 Mine Hit Workflow:")
    
    # Create game with many mines
    print("\n  Step 1: Create Game (20 mines)")
    response = client.post(
        '/api/games/mines/create/',
        data=json.dumps({
            'bet_amount': '10.00',
            'mine_count': 20
        }),
        content_type='application/json'
    )
    game_id = response.json()['game_id']
    print(f"    ✓ Game created: ID={game_id}")
    
    # Hit a mine
    print("\n  Step 2: Hit Mine")
    game = MinesGame.objects.get(id=game_id)
    mine_pos = game.mine_positions[0]
    
    response = client.post(
        f'/api/games/mines/{game_id}/open/',
        data=json.dumps({'row': mine_pos[0], 'col': mine_pos[1]}),
        content_type='application/json'
    )
    data = response.json()
    
    print(f"    ✓ Hit mine at ({mine_pos[0]}, {mine_pos[1]})")
    print(f"    ✓ Is mine: {data['is_mine']}")
    print(f"    ✓ Game state: {data['game_state']}")
    print(f"    ✓ Verification data included: {'verification' in data}")
    
    assert data['is_mine'] == True
    assert data['game_state'] == 'lost'
    assert 'mine_positions' in data
    assert 'verification' in data
    
    print("\n  ✓ Mine hit workflow completed successfully")


def cleanup():
    """Clean up test data"""
    print_section("8. Cleanup")
    
    # Delete test games
    deleted_count = MinesGame.objects.filter(
        user__username='mines_api_test_user'
    ).delete()[0]
    print(f"\n✓ Deleted {deleted_count} test games")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Mines Game API Test Suite")
    print("=" * 60)
    
    try:
        game_id = test_create_game()
        test_get_game(game_id)
        test_open_cell(game_id)
        test_cashout(game_id)
        test_verify_game(game_id)
        test_complete_workflow()
        test_mine_hit_workflow()
        cleanup()
        
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
