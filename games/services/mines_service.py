"""
Mines Game Service - business logic for Mines game.
Follows Single Responsibility Principle.
"""
import logging
from decimal import Decimal
from typing import Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import User
from wallet.services import WalletService, InsufficientFundsError
from games.models import MinesGame
from .provably_fair import ProvablyFairService

logger = logging.getLogger('games')


class MinesGameService:
    """
    Service for Mines game operations.
    All methods use database transactions for atomicity.
    """
    
    # Grid configuration
    GRID_SIZE = 5
    TOTAL_CELLS = GRID_SIZE * GRID_SIZE  # 25 cells
    
    # Mine count limits
    MIN_MINES = 3
    MAX_MINES = 20
    
    @staticmethod
    def validate_bet_amount(amount: Decimal) -> None:
        """
        Validate bet amount.
        
        Args:
            amount: Bet amount to validate
            
        Raises:
            ValidationError: If amount is invalid
        """
        if not isinstance(amount, Decimal):
            try:
                amount = Decimal(str(amount))
            except:
                raise ValidationError("Неверный формат суммы ставки")
        
        if amount <= 0:
            raise ValidationError("Сумма ставки должна быть больше нуля")
        
        if amount > Decimal('999999.99'):
            raise ValidationError("Сумма ставки слишком большая")
    
    @staticmethod
    def validate_mine_count(mine_count: int) -> None:
        """
        Validate mine count.
        
        Args:
            mine_count: Number of mines
            
        Raises:
            ValidationError: If mine count is invalid
        """
        if not isinstance(mine_count, int):
            raise ValidationError("Количество мин должно быть целым числом")
        
        if mine_count < MinesGameService.MIN_MINES or mine_count > MinesGameService.MAX_MINES:
            raise ValidationError(
                f"Количество мин должно быть от {MinesGameService.MIN_MINES} "
                f"до {MinesGameService.MAX_MINES}"
            )
    
    @staticmethod
    def validate_cell_coordinates(row: int, col: int) -> None:
        """
        Validate cell coordinates.
        
        Args:
            row: Row index (0-4)
            col: Column index (0-4)
            
        Raises:
            ValidationError: If coordinates are invalid
        """
        if not isinstance(row, int) or not isinstance(col, int):
            raise ValidationError("Координаты клетки должны быть целыми числами")
        
        if row < 0 or row >= MinesGameService.GRID_SIZE:
            raise ValidationError(
                f"Номер строки должен быть от 0 до {MinesGameService.GRID_SIZE - 1}"
            )
        
        if col < 0 or col >= MinesGameService.GRID_SIZE:
            raise ValidationError(
                f"Номер столбца должен быть от 0 до {MinesGameService.GRID_SIZE - 1}"
            )
    
    @staticmethod
    @transaction.atomic
    def create_game(
        user: User,
        bet_amount: Decimal,
        mine_count: int,
        client_seed: Optional[str] = None
    ) -> MinesGame:
        """
        Create new Mines game.
        
        Steps:
        1. Validate bet_amount and mine_count
        2. Check user has sufficient balance
        3. Place bet via WalletService
        4. Generate server_seed and client_seed
        5. Generate mine positions using ProvablyFair
        6. Create MinesGame instance
        7. Return game
        
        Args:
            user: User instance
            bet_amount: Bet amount
            mine_count: Number of mines (3-20)
            client_seed: Optional client seed (auto-generated if None)
            
        Returns:
            MinesGame instance with state=ACTIVE
            
        Raises:
            ValidationError: Invalid parameters
            InsufficientFundsError: Not enough balance
        """
        # Validate parameters
        MinesGameService.validate_bet_amount(bet_amount)
        MinesGameService.validate_mine_count(mine_count)
        
        logger.info(
            f"Creating Mines game for {user.username}: "
            f"bet={bet_amount}, mines={mine_count}"
        )
        
        # Check balance
        balance = WalletService.get_balance(user)
        if balance < bet_amount:
            raise InsufficientFundsError(
                f"Недостаточно средств. Баланс: {balance} ₽, требуется: {bet_amount} ₽"
            )
        
        # Place bet
        WalletService.place_bet(
            user,
            bet_amount,
            description=f'Ставка в Mines ({mine_count} мин)'
        )
        
        # Generate provably fair seeds
        server_seed = ProvablyFairService.generate_server_seed()
        server_seed_hash = ProvablyFairService.hash_seed(server_seed)
        
        if client_seed is None:
            client_seed = ProvablyFairService.generate_client_seed()
        
        # Get user's nonce (number of games played)
        nonce = MinesGame.objects.filter(user=user).count()
        
        # Generate mine positions
        mine_positions_tuples = ProvablyFairService.generate_mine_positions(
            server_seed=server_seed,
            client_seed=client_seed,
            nonce=nonce,
            mine_count=mine_count
        )
        
        # Convert tuples to lists for JSON storage
        mine_positions = [[row, col] for row, col in mine_positions_tuples]
        
        # Create game
        game = MinesGame.objects.create(
            user=user,
            bet_amount=bet_amount,
            mine_count=mine_count,
            state=MinesGame.GameState.ACTIVE,
            server_seed=server_seed,
            client_seed=client_seed,
            nonce=nonce,
            server_seed_hash=server_seed_hash,
            mine_positions=mine_positions,
            current_multiplier=Decimal('1.0')
        )
        
        logger.info(
            f"Mines game created: id={game.id}, "
            f"server_seed_hash={server_seed_hash[:16]}..."
        )
        
        return game
    
    @staticmethod
    def calculate_multiplier(mine_count: int, opened_safe_cells: int) -> Decimal:
        """
        Calculate current multiplier based on mines and opened cells.
        
        Formula from design.md:
        multiplier = product of (25 - i) / (25 - mine_count - i) for i in range(opened_safe_cells)
        
        Example:
        - mine_count=5, opened=0: multiplier=1.0
        - mine_count=5, opened=1: multiplier=1.25 (25/20)
        - mine_count=5, opened=2: multiplier=1.58 (25/20 * 24/19)
        
        Args:
            mine_count: Number of mines
            opened_safe_cells: Number of safe cells opened
            
        Returns:
            Current multiplier
        """
        if opened_safe_cells == 0:
            return Decimal('1.0')
        
        multiplier = Decimal('1.0')
        total_cells = MinesGameService.TOTAL_CELLS
        
        for i in range(opened_safe_cells):
            numerator = Decimal(total_cells - i)
            denominator = Decimal(total_cells - mine_count - i)
            multiplier *= numerator / denominator
        
        return multiplier.quantize(Decimal('0.01'))
    
    @staticmethod
    @transaction.atomic
    def open_cell(game: MinesGame, row: int, col: int) -> dict:
        """
        Open a cell in the game.
        
        Steps:
        1. Validate game is ACTIVE
        2. Validate cell coordinates (0-4)
        3. Check cell not already opened
        4. Check if cell has mine
        5. If mine: set state=LOST, reveal all mines, return result
        6. If safe: add to opened_cells, calculate new multiplier, return result
        
        Args:
            game: MinesGame instance
            row: Row index (0-4)
            col: Column index (0-4)
            
        Returns:
            {
                'is_mine': bool,
                'multiplier': Decimal,
                'game_state': str,
                'mine_positions': list (if game ended),
                'opened_cells': list
            }
            
        Raises:
            ValidationError: Invalid operation
        """
        # Validate game is active
        if not game.is_active():
            raise ValidationError(
                f"Игра уже завершена со статусом: {game.get_state_display()}"
            )
        
        # Validate coordinates
        MinesGameService.validate_cell_coordinates(row, col)
        
        # Check cell not already opened
        if game.is_cell_opened(row, col):
            raise ValidationError(f"Клетка ({row}, {col}) уже открыта")
        
        logger.info(
            f"Opening cell ({row}, {col}) in game {game.id} "
            f"for user {game.user.username}"
        )
        
        # Check if cell has mine
        is_mine = [row, col] in game.mine_positions
        
        if is_mine:
            # Hit mine - game over
            game.state = MinesGame.GameState.LOST
            game.ended_at = timezone.now()
            game.save()
            
            logger.info(
                f"Mine hit at ({row}, {col}) in game {game.id}. Game lost."
            )
            
            return {
                'is_mine': True,
                'multiplier': Decimal('0.0'),
                'game_state': game.state,
                'mine_positions': game.mine_positions,
                'opened_cells': game.opened_cells,
                'server_seed': game.server_seed,  # Reveal for verification
                'server_seed_hash': game.server_seed_hash,
                'client_seed': game.client_seed,
                'nonce': game.nonce
            }
        else:
            # Safe cell - add to opened cells
            game.opened_cells.append([row, col])
            
            # Calculate new multiplier
            opened_count = game.get_opened_cells_count()
            game.current_multiplier = MinesGameService.calculate_multiplier(
                game.mine_count,
                opened_count
            )
            
            game.save()
            
            logger.info(
                f"Safe cell opened at ({row}, {col}) in game {game.id}. "
                f"Multiplier: {game.current_multiplier}x"
            )
            
            return {
                'is_mine': False,
                'multiplier': game.current_multiplier,
                'game_state': game.state,
                'opened_cells': game.opened_cells,
                'opened_count': opened_count,
                'safe_cells_remaining': game.get_safe_cells_count() - opened_count
            }
    
    @staticmethod
    @transaction.atomic
    def cashout(game: MinesGame) -> Decimal:
        """
        Cash out current winnings.
        
        Steps:
        1. Validate game is ACTIVE
        2. Validate at least one cell opened
        3. Calculate winnings = bet_amount * current_multiplier
        4. Add winnings via WalletService
        5. Set state=CASHED_OUT
        6. Set ended_at timestamp
        7. Return winnings amount
        
        Args:
            game: MinesGame instance
            
        Returns:
            Winnings amount
            
        Raises:
            ValidationError: Game not active or no cells opened
        """
        # Validate game is active
        if not game.is_active():
            raise ValidationError(
                f"Игра уже завершена со статусом: {game.get_state_display()}"
            )
        
        # Validate at least one cell opened
        if not game.can_cashout():
            raise ValidationError("Нельзя забрать выигрыш - не открыто ни одной клетки")
        
        # Calculate winnings
        winnings = game.bet_amount * game.current_multiplier
        
        logger.info(
            f"Cashing out game {game.id} for user {game.user.username}: "
            f"bet={game.bet_amount}, multiplier={game.current_multiplier}x, "
            f"winnings={winnings}"
        )
        
        # Add winnings to balance
        WalletService.add_winnings(
            game.user,
            winnings,
            description=f'Выигрыш в Mines (множитель {game.current_multiplier}x)'
        )
        
        # Update game state
        game.state = MinesGame.GameState.CASHED_OUT
        game.ended_at = timezone.now()
        game.save()
        
        logger.info(f"Game {game.id} cashed out successfully. Winnings: {winnings}")
        
        return winnings
    
    @staticmethod
    def get_verification_data(game: MinesGame) -> dict:
        """
        Get provably fair verification data.
        
        Only available after game ends.
        
        Args:
            game: MinesGame instance
            
        Returns:
            {
                'server_seed': str,
                'server_seed_hash': str,
                'client_seed': str,
                'nonce': int,
                'mine_count': int,
                'mine_positions': list,
                'is_valid': bool
            }
            
        Raises:
            ValidationError: Game still active
        """
        if not game.is_ended():
            raise ValidationError("Данные для верификации доступны только после завершения игры")
        
        # Verify positions match seeds
        is_valid = ProvablyFairService.verify_mine_positions(
            server_seed=game.server_seed,
            client_seed=game.client_seed,
            nonce=game.nonce,
            mine_count=game.mine_count,
            claimed_positions=[tuple(pos) for pos in game.mine_positions]
        )
        
        return {
            'server_seed': game.server_seed,
            'server_seed_hash': game.server_seed_hash,
            'client_seed': game.client_seed,
            'nonce': game.nonce,
            'mine_count': game.mine_count,
            'mine_positions': game.mine_positions,
            'is_valid': is_valid
        }
