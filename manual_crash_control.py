"""
Manual control for Crash game rounds
"""
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from games.services.crash_service import CrashGameService
from games.models import CrashRound

print("=" * 60)
print("CRASH GAME MANUAL CONTROL")
print("=" * 60)

# Get current round
current_round = CrashGameService.get_current_round()

if not current_round:
    print("\nNo active round. Creating new round...")
    current_round = CrashGameService.start_new_round()
    print(f"✓ Round created: {current_round.round_id}")
    print(f"  Crash Point: {current_round.crash_point}x")
    print(f"  Status: {current_round.status}")

print(f"\nCurrent Round: {current_round.round_id}")
print(f"Status: {current_round.status}")
print(f"Crash Point: {current_round.crash_point}x")

if current_round.is_waiting():
    print("\n✓ Round is WAITING")
    print("\nActivating round in 3 seconds...")
    time.sleep(3)
    
    CrashGameService.activate_round(current_round)
    print("✓ Round ACTIVATED!")
    
    print("\nMultiplier will grow from 1.00x to crash point...")
    print("Players can now place bets and cashout!")
    print("\nPress Ctrl+C to stop")
    
    try:
        while True:
            current_round.refresh_from_db()
            if current_round.is_active():
                multiplier = CrashGameService.get_current_multiplier(current_round)
                print(f"\rMultiplier: {multiplier:.2f}x / {current_round.crash_point}x", end='', flush=True)
                
                # Check if reached crash point
                if multiplier >= current_round.crash_point:
                    print(f"\n\n💥 CRASH at {current_round.crash_point}x!")
                    CrashGameService.crash_round(current_round)
                    break
                    
                time.sleep(0.5)
            else:
                break
                
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        
elif current_round.is_active():
    print("\n✓ Round is ACTIVE")
    multiplier = CrashGameService.get_current_multiplier(current_round)
    print(f"Current Multiplier: {multiplier:.2f}x")
    
elif current_round.is_crashed():
    print("\n✓ Round is CRASHED")
    print("Creating new round...")
    new_round = CrashGameService.start_new_round()
    print(f"✓ New round: {new_round.round_id}")
    print(f"  Crash Point: {new_round.crash_point}x")

print("\n" + "=" * 60)
print("Open browser: http://localhost:8000/crash/")
print("=" * 60)
