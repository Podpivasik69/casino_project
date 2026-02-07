"""
Test RTP (Return to Player) for Slots game.
Target RTP: 80-85% for 5-reel mode
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from games.services.slots_service import SlotsGameService
from wallet.services import WalletService

User = get_user_model()


def test_rtp_5_reels(num_spins=1000, bet_amount=100):
    """
    Test RTP for 5-reel slots over many spins.
    
    Args:
        num_spins: Number of spins to simulate
        bet_amount: Bet amount per spin
    
    Expected:
        RTP should be between 80-85%
    """
    print(f"\n{'='*60}")
    print(f"SLOTS RTP TEST - 5 REELS")
    print(f"{'='*60}")
    print(f"Spins: {num_spins}")
    print(f"Bet per spin: {bet_amount} RUB")
    print(f"Total wagered: {num_spins * bet_amount} RUB")
    print(f"{'='*60}\n")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='rtp_test_user',
        defaults={'email': 'rtp@test.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Give user enough balance
    initial_balance = Decimal(str(num_spins * bet_amount * 2))
    user.profile.balance = initial_balance
    user.profile.save()
    
    total_bet = Decimal('0')
    total_win = Decimal('0')
    
    # Track results
    results = {
        'total_loss': 0,      # multiplier = 0
        'partial_loss': 0,    # 0 < multiplier < 1.0
        'return': 0,          # multiplier = 1.0
        'small_win': 0,       # 1.0 < multiplier < 5.0
        'medium_win': 0,      # 5.0 <= multiplier < 10.0
        'big_win': 0,         # 10.0 <= multiplier < 20.0
        'jackpot': 0,         # multiplier >= 20.0
    }
    
    multipliers = []
    
    print("Running spins...")
    for i in range(num_spins):
        try:
            # Refresh user balance
            user.refresh_from_db()
            
            # Create game
            game = SlotsGameService.create_and_play_game(
                user=user,
                bet_amount=Decimal(str(bet_amount)),
                reels_count=5
            )
            
            total_bet += game.bet_amount
            total_win += game.win_amount
            
            multiplier = float(game.multiplier)
            multipliers.append(multiplier)
            
            # Categorize result
            if multiplier == 0:
                results['total_loss'] += 1
            elif multiplier < 1.0:
                results['partial_loss'] += 1
            elif multiplier == 1.0:
                results['return'] += 1
            elif multiplier < 5.0:
                results['small_win'] += 1
            elif multiplier < 10.0:
                results['medium_win'] += 1
            elif multiplier < 20.0:
                results['big_win'] += 1
            else:
                results['jackpot'] += 1
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                current_rtp = (float(total_win) / float(total_bet)) * 100
                print(f"  {i + 1}/{num_spins} spins - Current RTP: {current_rtp:.2f}%")
        
        except Exception as e:
            print(f"Error on spin {i + 1}: {e}")
            continue
    
    # Calculate final RTP
    rtp = (float(total_win) / float(total_bet)) * 100 if total_bet > 0 else 0
    profit = float(total_win - total_bet)
    profit_percent = (profit / float(total_bet)) * 100 if total_bet > 0 else 0
    
    # Calculate statistics
    avg_multiplier = sum(multipliers) / len(multipliers) if multipliers else 0
    max_multiplier = max(multipliers) if multipliers else 0
    min_multiplier = min(multipliers) if multipliers else 0
    
    # Print results
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total bet:     {total_bet:,.2f} ₽")
    print(f"Total win:     {total_win:,.2f} ₽")
    print(f"Profit/Loss:   {profit:+,.2f} ₽ ({profit_percent:+.2f}%)")
    print(f"\n{'='*60}")
    print(f"RTP: {rtp:.2f}%")
    print(f"{'='*60}")
    
    # Check if RTP is in target range
    if 80 <= rtp <= 85:
        print(f"✅ RTP is in target range (80-85%)")
    elif rtp < 80:
        print(f"⚠️  RTP is too low (< 80%) - Players lose too much")
    else:
        print(f"❌ RTP is too high (> 85%) - Casino loses money!")
    
    print(f"\n{'='*60}")
    print(f"MULTIPLIER STATISTICS")
    print(f"{'='*60}")
    print(f"Average:  {avg_multiplier:.3f}x")
    print(f"Maximum:  {max_multiplier:.3f}x")
    print(f"Minimum:  {min_multiplier:.3f}x")
    
    print(f"\n{'='*60}")
    print(f"RESULT DISTRIBUTION")
    print(f"{'='*60}")
    for result_type, count in results.items():
        percentage = (count / num_spins) * 100
        print(f"{result_type:15s}: {count:4d} ({percentage:5.1f}%)")
    
    print(f"\n{'='*60}")
    print(f"ANALYSIS")
    print(f"{'='*60}")
    
    # Calculate loss rate
    loss_rate = (results['total_loss'] + results['partial_loss']) / num_spins * 100
    win_rate = (results['small_win'] + results['medium_win'] + results['big_win'] + results['jackpot']) / num_spins * 100
    
    print(f"Loss rate:   {loss_rate:.1f}% (total + partial losses)")
    print(f"Win rate:    {win_rate:.1f}% (any win > 1.0x)")
    print(f"Return rate: {results['return'] / num_spins * 100:.1f}% (break-even)")
    
    print(f"\n{'='*60}\n")
    
    return rtp


def test_rtp_3_reels(num_spins=1000, bet_amount=100):
    """
    Test RTP for 3-reel slots over many spins.
    
    Args:
        num_spins: Number of spins to simulate
        bet_amount: Bet amount per spin
    
    Expected:
        RTP should be between 82-85%
    """
    print(f"\n{'='*60}")
    print(f"SLOTS RTP TEST - 3 REELS")
    print(f"{'='*60}")
    print(f"Spins: {num_spins}")
    print(f"Bet per spin: {bet_amount} ₽")
    print(f"Total wagered: {num_spins * bet_amount} ₽")
    print(f"{'='*60}\n")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='rtp_test_user_3reels',
        defaults={'email': 'rtp3@test.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Give user enough balance
    initial_balance = Decimal(str(num_spins * bet_amount * 2))
    user.profile.balance = initial_balance
    user.profile.save()
    
    total_bet = Decimal('0')
    total_win = Decimal('0')
    
    multipliers = []
    
    print("Running spins...")
    for i in range(num_spins):
        try:
            # Refresh user balance
            user.refresh_from_db()
            
            # Create game
            game = SlotsGameService.create_and_play_game(
                user=user,
                bet_amount=Decimal(str(bet_amount)),
                reels_count=3
            )
            
            total_bet += game.bet_amount
            total_win += game.win_amount
            
            multipliers.append(float(game.multiplier))
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                current_rtp = (float(total_win) / float(total_bet)) * 100
                print(f"  {i + 1}/{num_spins} spins - Current RTP: {current_rtp:.2f}%")
        
        except Exception as e:
            print(f"Error on spin {i + 1}: {e}")
            continue
    
    # Calculate final RTP
    rtp = (float(total_win) / float(total_bet)) * 100 if total_bet > 0 else 0
    profit = float(total_win - total_bet)
    profit_percent = (profit / float(total_bet)) * 100 if total_bet > 0 else 0
    
    # Print results
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total bet:     {total_bet:,.2f} ₽")
    print(f"Total win:     {total_win:,.2f} ₽")
    print(f"Profit/Loss:   {profit:+,.2f} ₽ ({profit_percent:+.2f}%)")
    print(f"\n{'='*60}")
    print(f"RTP: {rtp:.2f}%")
    print(f"{'='*60}")
    
    # Check if RTP is in target range
    if 82 <= rtp <= 85:
        print(f"✅ RTP is in target range (82-85%)")
    elif rtp < 82:
        print(f"⚠️  RTP is too low (< 82%) - Players lose too much")
    else:
        print(f"❌ RTP is too high (> 85%) - Casino loses money!")
    
    print(f"\n{'='*60}\n")
    
    return rtp


if __name__ == '__main__':
    print("\n" + "="*60)
    print("SLOTS RTP TESTING SUITE")
    print("="*60)
    
    # Test 5-reel mode (main concern)
    rtp_5 = test_rtp_5_reels(num_spins=1000, bet_amount=100)
    
    # Test 3-reel mode for comparison
    rtp_3 = test_rtp_3_reels(num_spins=1000, bet_amount=100)
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"5-reel RTP: {rtp_5:.2f}% (target: 80-85%)")
    print(f"3-reel RTP: {rtp_3:.2f}% (target: 82-85%)")
    print("="*60)
    
    if 80 <= rtp_5 <= 85 and 82 <= rtp_3 <= 85:
        print("✅ ALL TESTS PASSED - RTP is balanced!")
    else:
        print("❌ TESTS FAILED - RTP needs adjustment!")
    
    print("="*60 + "\n")
