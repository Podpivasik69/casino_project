"""
Detailed test of Crash API endpoints with authentication
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from django.test import Client
from users.models import User, Profile
from games.services.crash_service import CrashGameService
from decimal import Decimal
import json

print("=" * 60)
print("CRASH API DETAILED TEST")
print("=" * 60)

# Create test client
client = Client()

# Create or get test user
print("\n1. Setting up test user...")
user, created = User.objects.get_or_create(
    username='crash_api_test',
    defaults={'email': 'crashapi@test.com'}
)

if created:
    user.set_password('test123')
    user.save()

# Ensure profile with balance
profile, _ = Profile.objects.get_or_create(user=user)
if profile.balance < 100:
    profile.balance = Decimal('1000.00')
    profile.save()

print(f"✓ User: {user.username}")
print(f"✓ Balance: {profile.balance} ₽")

# Login
print("\n2. Logging in...")
login_success = client.login(username='crash_api_test', password='test123')
print(f"✓ Login: {'Success' if login_success else 'Failed'}")

if not login_success:
    print("✗ Cannot proceed without login")
    exit(1)

# Create a round
print("\n3. Creating round...")
round_instance = CrashGameService.start_new_round()
print(f"✓ Round: {round_instance.round_id}")
print(f"  Status: {round_instance.status}")

# Test GET /api/games/crash/current/
print("\n4. Testing GET /api/games/crash/current/")
response = client.get('/api/games/crash/current/')
print(f"  Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✓ Response:")
    print(f"  Round ID: {data.get('round_id')}")
    print(f"  Status: {data.get('status')}")
    if data.get('status') == 'waiting':
        print(f"  Seconds until start: {data.get('seconds_until_start')}")
else:
    print(f"✗ Error: {response.content}")

# Test POST /api/games/crash/bet/
print("\n5. Testing POST /api/games/crash/bet/")
bet_data = {
    'amount': '10.00',
    'auto_cashout_target': '2.00'
}
response = client.post(
    '/api/games/crash/bet/',
    data=json.dumps(bet_data),
    content_type='application/json'
)
print(f"  Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✓ Bet placed:")
    print(f"  Bet ID: {data.get('bet_id')}")
    print(f"  Amount: {data.get('bet_amount')} ₽")
    print(f"  Auto cashout: {data.get('auto_cashout_target')}x")
    print(f"  New balance: {data.get('balance')} ₽")
    bet_id = data.get('bet_id')
else:
    print(f"✗ Error: {response.json()}")
    bet_id = None

# Activate round
if bet_id:
    print("\n6. Activating round...")
    CrashGameService.activate_round(round_instance)
    print(f"✓ Round activated")
    
    # Test GET /api/games/crash/current/ again
    print("\n7. Testing GET /api/games/crash/current/ (active)")
    response = client.get('/api/games/crash/current/')
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Response:")
        print(f"  Status: {data.get('status')}")
        print(f"  Multiplier: {data.get('current_multiplier')}x")
        print(f"  User bets: {len(data.get('user_bets', []))}")
    
    # Test POST /api/games/crash/cashout/
    print("\n8. Testing POST /api/games/crash/cashout/")
    cashout_data = {'bet_id': bet_id}
    response = client.post(
        '/api/games/crash/cashout/',
        data=json.dumps(cashout_data),
        content_type='application/json'
    )
    print(f"  Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Cashed out:")
        print(f"  Multiplier: {data.get('cashout_multiplier')}x")
        print(f"  Win amount: {data.get('win_amount')} ₽")
        print(f"  New balance: {data.get('balance')} ₽")
    else:
        print(f"✗ Error: {response.json()}")

# Test GET /api/games/crash/history/
print("\n9. Testing GET /api/games/crash/history/")
response = client.get('/api/games/crash/history/')
print(f"  Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    rounds = data.get('rounds', [])
    print(f"✓ History loaded: {len(rounds)} rounds")
    if rounds:
        print(f"  Latest crash: {rounds[0].get('crash_point')}x")

print("\n" + "=" * 60)
print("✓ ALL API TESTS COMPLETE")
print("=" * 60)
print("\nYou can now test in browser:")
print("http://localhost:8000/crash/")
print("\nLogin with:")
print("  Username: crash_api_test")
print("  Password: test123")
