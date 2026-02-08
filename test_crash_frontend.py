"""
Quick test to verify Crash game frontend loads and works
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("CRASH FRONTEND TEST")
print("=" * 60)

# Test 1: Page loads
print("\n1. Testing page load...")
try:
    response = requests.get(f"{BASE_URL}/crash/", timeout=5)
    if response.status_code == 200:
        print(f"✓ Page loads successfully (status: {response.status_code})")
        if "Crash" in response.text and "multiplier" in response.text.lower():
            print("✓ Page contains expected content")
        else:
            print("⚠ Page may be missing some content")
    else:
        print(f"✗ Page failed to load (status: {response.status_code})")
except Exception as e:
    print(f"✗ Error loading page: {e}")

# Test 2: API endpoints accessible
print("\n2. Testing API endpoints...")
try:
    response = requests.get(f"{BASE_URL}/api/games/crash/current/")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Current round API works")
        print(f"  Status: {data.get('status')}")
        print(f"  Multiplier: {data.get('current_multiplier')}x")
    else:
        print(f"✗ API failed (status: {response.status_code})")
except Exception as e:
    print(f"✗ Error calling API: {e}")

print("\n" + "=" * 60)
print("✓ FRONTEND TEST COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Open http://localhost:8000/crash/ in your browser")
print("2. Login with a test user")
print("3. Try placing a bet and cashing out")
print("4. Watch the multiplier grow in real-time")
