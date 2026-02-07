"""Simple RTP test for 5-reel slots"""
import os, django, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from games.services.slots_service import SlotsGameService

User = get_user_model()

# Get or create test user
user, _ = User.objects.get_or_create(
    username='rtp_test_5reels_v2',
    defaults={'email': 'rtp5v2@test.com'}
)
user.profile.balance = Decimal('200000')
user.profile.save()

total_bet = Decimal('0')
total_win = Decimal('0')
num_spins = 1000

print(f"\nTesting 5-reel RTP with {num_spins} spins...")

for i in range(num_spins):
    user.refresh_from_db()
    game = SlotsGameService.create_and_play_game(
        user=user,
        bet_amount=Decimal('100'),
        reels_count=5
    )
    total_bet += game.bet_amount
    total_win += game.win_amount
    
    if (i + 1) % 100 == 0:
        current_rtp = (float(total_win) / float(total_bet)) * 100
        print(f"  {i + 1}/{num_spins} - RTP: {current_rtp:.2f}%")

rtp = (float(total_win) / float(total_bet)) * 100
profit = float(total_win - total_bet)

print(f"\n{'='*50}")
print(f"FINAL RESULTS")
print(f"{'='*50}")
print(f"Total bet:  {float(total_bet):,.2f}")
print(f"Total win:  {float(total_win):,.2f}")
print(f"Profit:     {profit:+,.2f} ({(profit/float(total_bet))*100:+.2f}%)")
print(f"\nRTP: {rtp:.2f}%")
print(f"{'='*50}")

if 80 <= rtp <= 85:
    print("SUCCESS: RTP is in target range (80-85%)")
elif rtp < 80:
    print("WARNING: RTP too low (< 80%)")
else:
    print("ERROR: RTP too high (> 85%) - Casino loses money!")
