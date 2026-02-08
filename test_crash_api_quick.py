"""
Quick Crash API Test
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from games.services.crash_service import CrashGameService

User = get_user_model()

print("=" * 60)
print("CRASH API QUICK TEST")
print("=" * 60)

# Create test client
client = Client()

# Get or create test user
user, created = User.objects.get_or_create(
    username='test_crash_api',
    defaults={'email': 'test_crash_api@example.com'}
)

if created:
    user.set_password('testpass123')
    user.save()

# Ensure profile exists
from users.models import Profile
from decimal import Decimal
profile, _ = Profile.objects.get_or_create(user=user)
profile.balance = Decimal('1000.00')
profile.save()

# Login
client.login(username='test_crash_api', password='testpass123')

# Create a round
print("\n1. Creating round...")
round_instance = CrashGameService.start_new_round()
print(f"✓ Round created: {round_instance.round_id}")

# Test GET /current/
print("\n2. Testing GET /api/games/crash/current/")
response = client.get('/api/games/crash/current/')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✓ Response: {data.get('status')}")
else:
    print(f"✗ Error: {response.content}")

# Test POST /bet/
print("\n3. Testing POST /api/games/crash/bet/")
response = client.post(
    '/api/games/crash/bet/',
    data={'amount': '10.00', 'auto_cashout_target': '2.00'},
    content_type='application/json'
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✓ Bet placed: {data.get('bet_id')}")
    bet_id = data.get('bet_id')
else:
    print(f"✗ Error: {response.content}")
    bet_id = None

# Activate round
print("\n4. Activating round...")
CrashGameService.activate_round(round_instance)
print("✓ Round activated")

# Test POST /cashout/
if bet_id:
    print("\n5. Testing POST /api/games/crash/cashout/")
    response = client.post(
        '/api/games/crash/cashout/',
        data={'bet_id': bet_id},
        content_type='application/json'
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Cashed out: {data.get('win_amount')} at {data.get('cashout_multiplier')}x")
    else:
        print(f"✗ Error: {response.content}")

# Test GET /history/
print("\n6. Testing GET /api/games/crash/history/")
response = client.get('/api/games/crash/history/')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✓ History loaded: {len(data.get('rounds', []))} rounds")
else:
    print(f"✗ Error: {response.content}")

print("\n" + "=" * 60)
print("✓ ALL API TESTS COMPLETED")
print("=" * 60)
