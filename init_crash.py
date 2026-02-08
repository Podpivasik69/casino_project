"""
Initialize first crash round
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from games.services.crash_service import CrashGameService

# Create first round
round_instance = CrashGameService.start_new_round()
print(f"✓ First round created!")
print(f"  Round ID: {round_instance.round_id}")
print(f"  Crash Point: {round_instance.crash_point}x")
print(f"  Status: {round_instance.status}")
print(f"\nYou can now visit http://localhost:8000/crash/")
