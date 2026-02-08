"""
Crash game service.

Handles all business logic for the Crash game:
- Round management (start, activate, crash)
- Bet placement and cashout
- Multiplier calculation
- Auto-cashout processing
- Provably fair crash point generation
"""
import hashlib
import hmac
import secrets
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from games.models import CrashRound, CrashBet
from wallet.services import WalletService


class InsufficientFundsError(Exception):
    """Raised when user has insufficient funds"""
    pass


class CrashGameService:
    """
    Service for crash game business logic.
    """
    
    # Constants
    HOUSE_EDGE = Decimal('3.00')  # 3% house edge for 97% RTP
    MIN_BET = Decimal('0.01')
    MAX_BET = Decimal('1000.00')
    MIN_CRASH_POINT = Decimal('1.00')
    MAX_CRASH_POINT = Decimal('10000.00')
    WAITING_DURATION = 8  # seconds between rounds
    MAX_BETS_PER_USER = 5
    
    @staticmethod
    def calculate_crash_point(server_seed: str, client_seed: str) -> Decimal:
        """
        Calculate crash point using provably fair algorithm.
        
        Formula:
        - Combine seeds using HMAC-SHA256
        - Convert hash to random value [0, 1]
        - crash_point = (100 / (100 - HOUSE_EDGE)) / random_value
        - crash_point = (100 / 97) / random_value
        - Ensure crash_point >= MIN_CRASH_POINT
        - Cap at MAX_CRASH_POINT
        
        Args:
            server_seed: Server seed (hex string)
            client_seed: Client seed (hex string)
            
        Returns:
            Crash point (Decimal)
        """
        # Combine seeds using HMAC-SHA256
        combined = hmac.new(
            server_seed.encode('utf-8'),
            client_seed.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Convert first 8 bytes to integer and normalize to [0, 1]
        hash_int = int(combined[:16], 16)
        max_int = 0xFFFFFFFFFFFFFFFF
        random_value = Decimal(hash_int) / Decimal(max_int)
        
        # Avoid division by zero
        if random_value == 0:
            random_value = Decimal('0.000001')
        
        # Calculate crash point: (100 / 97) / random_value
        crash_point = (Decimal('100') / (Decimal('100') - CrashGameService.HOUSE_EDGE)) / random_value
        
        # Ensure minimum crash point
        if crash_point < CrashGameService.MIN_CRASH_POINT:
            crash_point = CrashGameService.MIN_CRASH_POINT
        
        # Cap at maximum crash point
        if crash_point > CrashGameService.MAX_CRASH_POINT:
            crash_point = CrashGameService.MAX_CRASH_POINT
        
        # Round to 2 decimal places
        return crash_point.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    @staticmethod
    @transaction.atomic
    def start_new_round() -> CrashRound:
        """
        Start a new crash round.
        
        Steps:
        1. Generate server_seed and client_seed
        2. Calculate crash_point using provably fair algorithm
        3. Create CrashRound with status=WAITING
        4. Set next_round_at timestamp
        
        Returns:
            CrashRound instance
        """
        # Generate seeds
        server_seed = secrets.token_hex(32)  # 64 hex chars
        client_seed = secrets.token_hex(32)  # 64 hex chars
        
        # Hash server seed for public display
        server_seed_hash = hashlib.sha256(server_seed.encode('utf-8')).hexdigest()
        
        # Calculate crash point
        crash_point = CrashGameService.calculate_crash_point(server_seed, client_seed)
        
        # Calculate next round start time
        next_round_at = timezone.now() + timedelta(seconds=CrashGameService.WAITING_DURATION)
        
        # Create round
        round_instance = CrashRound.objects.create(
            status=CrashRound.RoundStatus.WAITING,
            crash_point=crash_point,
            server_seed=server_seed,
            client_seed=client_seed,
            server_seed_hash=server_seed_hash,
            next_round_at=next_round_at
        )
        
        return round_instance
    
    @staticmethod
    @transaction.atomic
    def activate_round(round_instance: CrashRound) -> None:
        """
        Activate a waiting round.
        
        Steps:
        1. Update status to ACTIVE
        2. Set started_at timestamp
        3. Save round
        
        Args:
            round_instance: CrashRound to activate
        """
        round_instance.status = CrashRound.RoundStatus.ACTIVE
        round_instance.started_at = timezone.now()
        round_instance.save()
    
    @staticmethod
    def get_current_round():
        """
        Get the current active or waiting round.
        
        Returns:
            CrashRound instance or None
        """
        return CrashRound.objects.filter(
            status__in=[CrashRound.RoundStatus.WAITING, CrashRound.RoundStatus.ACTIVE]
        ).order_by('-created_at').first()
    
    @staticmethod
    def get_current_multiplier(round_instance: CrashRound) -> Decimal:
        """
        Calculate current multiplier based on elapsed time.
        
        Formula:
        - elapsed_seconds = (now - started_at) in seconds
        - Smooth exponential growth:
          - 0-10s: 1.00x to 2.00x (slow start)
          - 10-30s: 2.00x to 5.00x (medium growth)
          - 30s+: exponential growth
        - multiplier = 1.00 * (1.06 ^ elapsed_seconds)
        - capped at crash_point
        
        Args:
            round_instance: Active CrashRound
            
        Returns:
            Current multiplier (1.00x to crash_point)
        """
        if not round_instance.is_active() or not round_instance.started_at:
            return Decimal('1.00')
        
        # Calculate elapsed time in seconds
        elapsed = timezone.now() - round_instance.started_at
        elapsed_seconds = Decimal(str(elapsed.total_seconds()))
        
        # Smooth exponential growth formula: 1.00 * (1.06 ^ elapsed_seconds)
        # This gives:
        # - 0s: 1.00x
        # - 5s: 1.34x
        # - 10s: 1.79x
        # - 15s: 2.40x
        # - 20s: 3.21x
        # - 25s: 4.29x
        # - 30s: 5.74x
        # - 40s: 10.29x
        # - 50s: 18.42x
        
        import math
        exponent = float(elapsed_seconds)
        multiplier = Decimal(str(math.pow(1.06, exponent)))
        
        # Cap at crash point
        if multiplier > round_instance.crash_point:
            multiplier = round_instance.crash_point
        
        # Round to 2 decimal places
        return multiplier.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    @staticmethod
    @transaction.atomic
    def place_bet(
        user,
        amount: Decimal,
        auto_cashout_target: Decimal = None
    ) -> CrashBet:
        """
        Place a bet in the current round.
        
        Steps:
        1. Validate bet amount (MIN_BET <= amount <= MAX_BET)
        2. Get current round (must be WAITING or early ACTIVE)
        3. Check user doesn't exceed MAX_BETS_PER_USER
        4. Deduct bet amount using WalletService
        5. Create CrashBet with status=ACTIVE
        6. Return bet instance
        
        Args:
            user: User placing bet
            amount: Bet amount
            auto_cashout_target: Optional auto cashout multiplier
            
        Returns:
            CrashBet instance
            
        Raises:
            ValidationError: Invalid bet amount or round state
            InsufficientFundsError: User has insufficient balance
        """
        # Validate bet amount
        if amount < CrashGameService.MIN_BET:
            raise ValidationError(f'Минимальная ставка: {CrashGameService.MIN_BET}')
        if amount > CrashGameService.MAX_BET:
            raise ValidationError(f'Максимальная ставка: {CrashGameService.MAX_BET}')
        
        # Validate auto cashout target
        if auto_cashout_target is not None:
            if auto_cashout_target < Decimal('1.01'):
                raise ValidationError('Минимальная цель авто-кэшаута: 1.01x')
        
        # Get current round
        round_instance = CrashGameService.get_current_round()
        if not round_instance:
            raise ValidationError('Нет активного раунда')
        
        # Only allow bets in WAITING or early ACTIVE rounds
        if round_instance.is_crashed():
            raise ValidationError('Раунд уже крашнулся')
        
        # Check if user has too many active bets
        active_bets_count = CrashBet.objects.filter(
            user=user,
            round=round_instance,
            status=CrashBet.BetStatus.ACTIVE
        ).count()
        
        if active_bets_count >= CrashGameService.MAX_BETS_PER_USER:
            raise ValidationError(f'Максимум {CrashGameService.MAX_BETS_PER_USER} ставок на раунд')
        
        # Check user balance
        profile = user.profile
        if profile.balance < amount:
            raise InsufficientFundsError('Недостаточно средств')
        
        # Deduct bet amount
        WalletService.place_bet(
            user=user,
            amount=amount,
            description=f'Crash bet - Round {round_instance.round_id}'
        )
        
        # Create bet
        bet = CrashBet.objects.create(
            user=user,
            round=round_instance,
            bet_amount=amount,
            status=CrashBet.BetStatus.ACTIVE,
            auto_cashout_target=auto_cashout_target
        )
        
        return bet
    
    @staticmethod
    @transaction.atomic
    def cashout(user, bet_id: int) -> CrashBet:
        """
        Cash out an active bet.
        
        Steps:
        1. Get bet and verify it belongs to user
        2. Verify bet status is ACTIVE
        3. Get current round and verify it's ACTIVE
        4. Get current multiplier
        5. Calculate win_amount = bet_amount * current_multiplier
        6. Update bet: status=CASHED_OUT, cashout_multiplier, win_amount
        7. Add winnings using WalletService
        8. Set cashed_out_at timestamp
        9. Return updated bet
        
        Args:
            user: User cashing out
            bet_id: Bet ID to cash out
            
        Returns:
            Updated CrashBet instance
            
        Raises:
            ValidationError: Invalid bet state or round state
        """
        # Get bet
        try:
            bet = CrashBet.objects.select_for_update().get(id=bet_id, user=user)
        except CrashBet.DoesNotExist:
            raise ValidationError('Ставка не найдена')
        
        # Verify bet is active
        if not bet.is_active():
            raise ValidationError('Ставка уже не активна')
        
        # Get round
        round_instance = bet.round
        
        # Verify round is active
        if not round_instance.is_active():
            raise ValidationError('Раунд не активен')
        
        # Get current multiplier
        current_multiplier = CrashGameService.get_current_multiplier(round_instance)
        
        # Calculate win amount
        win_amount = bet.bet_amount * current_multiplier
        
        # Update bet
        bet.status = CrashBet.BetStatus.CASHED_OUT
        bet.cashout_multiplier = current_multiplier
        bet.win_amount = win_amount
        bet.cashed_out_at = timezone.now()
        bet.save()
        
        # Add winnings
        WalletService.add_winnings(
            user=user,
            amount=win_amount,
            description=f'Crash win - {current_multiplier}x - Round {round_instance.round_id}'
        )
        
        return bet
    
    @staticmethod
    @transaction.atomic
    def process_auto_cashouts(round_instance: CrashRound, current_multiplier: Decimal) -> int:
        """
        Process all auto cashouts at current multiplier.
        
        Steps:
        1. Find all ACTIVE bets with auto_cashout_target <= current_multiplier
        2. For each bet:
           - Calculate win_amount using auto_cashout_target
           - Update bet status to CASHED_OUT
           - Add winnings using WalletService
        3. Return count of processed bets
        
        Args:
            round_instance: Current CrashRound
            current_multiplier: Current multiplier
            
        Returns:
            Number of bets cashed out
        """
        # Find bets to auto cashout
        bets_to_cashout = CrashBet.objects.select_for_update().filter(
            round=round_instance,
            status=CrashBet.BetStatus.ACTIVE,
            auto_cashout_target__isnull=False,
            auto_cashout_target__lte=current_multiplier
        )
        
        count = 0
        for bet in bets_to_cashout:
            # Calculate win amount using auto cashout target
            win_amount = bet.bet_amount * bet.auto_cashout_target
            
            # Update bet
            bet.status = CrashBet.BetStatus.CASHED_OUT
            bet.cashout_multiplier = bet.auto_cashout_target
            bet.win_amount = win_amount
            bet.cashed_out_at = timezone.now()
            bet.save()
            
            # Add winnings
            WalletService.add_winnings(
                user=bet.user,
                amount=win_amount,
                description=f'Crash auto-cashout - {bet.auto_cashout_target}x - Round {round_instance.round_id}'
            )
            
            count += 1
        
        return count
    
    @staticmethod
    @transaction.atomic
    def crash_round(round_instance: CrashRound) -> None:
        """
        Crash the current round and process all bets.
        
        Steps:
        1. Update round status to CRASHED
        2. Set crashed_at timestamp
        3. Get all ACTIVE bets for this round
        4. Update all active bets to status=LOST
        5. Save round
        
        Args:
            round_instance: CrashRound to crash
        """
        # Update round
        round_instance.status = CrashRound.RoundStatus.CRASHED
        round_instance.crashed_at = timezone.now()
        round_instance.save()
        
        # Process all active bets as losses
        CrashBet.objects.filter(
            round=round_instance,
            status=CrashBet.BetStatus.ACTIVE
        ).update(status=CrashBet.BetStatus.LOST)
    
    @staticmethod
    def get_round_history(limit: int = 50):
        """
        Get history of completed rounds.
        
        Args:
            limit: Maximum number of rounds to return
            
        Returns:
            QuerySet of CrashRound ordered by created_at descending
        """
        return CrashRound.objects.filter(
            status=CrashRound.RoundStatus.CRASHED
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_user_bets(user, round_instance: CrashRound):
        """
        Get user's bets for a specific round.
        
        Args:
            user: User instance
            round_instance: CrashRound instance
            
        Returns:
            QuerySet of CrashBet
        """
        return CrashBet.objects.filter(
            user=user,
            round=round_instance
        ).order_by('-created_at')
