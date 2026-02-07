"""
Dice game service.
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from games.models import DiceGame
from games.services.provably_fair import ProvablyFairService
from wallet.services import WalletService, InsufficientFundsError


class DiceGameService:
    """Service for Dice game logic."""
    
    # Game constants
    MIN_BET = Decimal('0.01')
    MAX_BET = Decimal('10000.00')
    WIN_MULTIPLIER = Decimal('6.00')
    LOSE_MULTIPLIER = Decimal('0.00')
    
    @classmethod
    def validate_bet(cls, bet_amount: Decimal) -> None:
        """
        Validate bet amount.
        
        Args:
            bet_amount: Bet amount to validate
            
        Raises:
            ValueError: If bet is invalid
        """
        if bet_amount < cls.MIN_BET:
            raise ValueError(f'Минимальная ставка: {cls.MIN_BET}')
        if bet_amount > cls.MAX_BET:
            raise ValueError(f'Максимальная ставка: {cls.MAX_BET}')
    
    @classmethod
    def validate_selected_number(cls, selected_number: int) -> None:
        """
        Validate selected number.
        
        Args:
            selected_number: Number selected by user (1-6)
            
        Raises:
            ValueError: If number is invalid
        """
        if not isinstance(selected_number, int):
            raise ValueError('Выбранное число должно быть целым числом')
        if selected_number < 1 or selected_number > 6:
            raise ValueError('Выбранное число должно быть от 1 до 6')
    
    @classmethod
    @transaction.atomic
    def create_and_play_game(
        cls,
        user,
        bet_amount: Decimal,
        selected_number: int,
        client_seed: str = None
    ) -> DiceGame:
        """
        Create and play a dice game.
        
        Args:
            user: User playing the game
            bet_amount: Amount to bet
            selected_number: Number selected by user (1-6)
            client_seed: Optional client seed for provably fair
            
        Returns:
            DiceGame instance
            
        Raises:
            ValueError: If validation fails
            Exception: If insufficient balance
        """
        # Validate inputs
        cls.validate_bet(bet_amount)
        cls.validate_selected_number(selected_number)
        
        # Place bet (this will check balance and deduct)
        WalletService.place_bet(
            user=user,
            amount=bet_amount,
            description=f'Ставка в Dice: {selected_number}'
        )
        
        # Generate provably fair seeds
        server_seed = ProvablyFairService.generate_server_seed()
        server_seed_hash = ProvablyFairService.hash_seed(server_seed)
        if not client_seed:
            client_seed = ProvablyFairService.generate_client_seed()
        nonce = 0
        
        # Generate random number (1-6)
        rolled_number = ProvablyFairService.generate_dice_roll(
            server_seed=server_seed,
            client_seed=client_seed,
            nonce=nonce
        )
        
        # Determine win/loss
        won = (rolled_number == selected_number)
        multiplier = cls.WIN_MULTIPLIER if won else cls.LOSE_MULTIPLIER
        
        # Create game record
        game = DiceGame.objects.create(
            user=user,
            bet_amount=bet_amount,
            selected_number=selected_number,
            rolled_number=rolled_number,
            multiplier=multiplier,
            won=won,
            server_seed=server_seed,
            client_seed=client_seed,
            nonce=nonce,
            server_seed_hash=server_seed_hash
        )
        
        # Add winnings if won
        if won:
            winnings = bet_amount * multiplier
            WalletService.add_winnings(
                user=user,
                amount=winnings,
                description=f'Выигрыш в Dice (выпало {rolled_number}, x{multiplier})'
            )
        
        return game
    
    @classmethod
    def get_user_games(cls, user, limit: int = 10):
        """
        Get user's recent dice games.
        
        Args:
            user: User to get games for
            limit: Maximum number of games to return
            
        Returns:
            QuerySet of DiceGame instances
        """
        return DiceGame.objects.filter(user=user).order_by('-created_at')[:limit]
    
    @classmethod
    def get_game_by_id(cls, game_id: int, user=None):
        """
        Get game by ID.
        
        Args:
            game_id: Game ID
            user: Optional user to filter by
            
        Returns:
            DiceGame instance or None
        """
        try:
            if user:
                return DiceGame.objects.get(id=game_id, user=user)
            return DiceGame.objects.get(id=game_id)
        except DiceGame.DoesNotExist:
            return None
    
    @classmethod
    def verify_game(cls, game: DiceGame) -> bool:
        """
        Verify game result using provably fair.
        
        Args:
            game: DiceGame instance
            
        Returns:
            True if verification passes
        """
        expected_roll = ProvablyFairService.generate_dice_roll(
            server_seed=game.server_seed,
            client_seed=game.client_seed,
            nonce=game.nonce
        )
        return expected_roll == game.rolled_number
