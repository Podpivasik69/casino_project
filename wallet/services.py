"""
Wallet service for managing user balance and transactions.
All operations are atomic and thread-safe.
"""
import logging
from decimal import Decimal
from typing import Optional
from django.db import transaction, models
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from users.models import User, Profile
from .models import Transaction

logger = logging.getLogger('wallet')


class InsufficientFundsError(Exception):
    """Raised when user doesn't have enough balance for operation"""
    pass


class WalletService:
    """
    Service for wallet operations.
    All methods use database transactions for atomicity.
    Follows Single Responsibility Principle - handles only wallet logic.
    """
    
    # Demo deposit amount (fixed for MVP)
    DEMO_DEPOSIT_AMOUNT = Decimal('500.00')
    
    @staticmethod
    def get_balance(user: User) -> Decimal:
        """
        Get current user balance.
        
        Args:
            user: User instance
            
        Returns:
            Current balance from Profile
            
        Raises:
            ValidationError: If profile doesn't exist
        """
        if not hasattr(user, 'profile'):
            logger.error(f"Profile not found for user: {user.username}")
            raise ValidationError("Профиль пользователя не найден")
        
        return user.profile.balance
    
    @staticmethod
    def validate_amount(amount: Decimal, operation: str = "operation") -> None:
        """
        Validate transaction amount.
        
        Args:
            amount: Amount to validate
            operation: Operation name for error message
            
        Raises:
            ValidationError: If amount is invalid
        """
        if not isinstance(amount, Decimal):
            try:
                amount = Decimal(str(amount))
            except:
                raise ValidationError(f"Неверный формат суммы для {operation}")
        
        if amount <= 0:
            raise ValidationError(f"Сумма {operation} должна быть больше нуля")
        
        if amount > Decimal('999999999.99'):
            raise ValidationError(f"Сумма {operation} слишком большая")
    
    @staticmethod
    @transaction.atomic
    def deposit(user: User, amount: Optional[Decimal] = None, description: str = '') -> Transaction:
        """
        Add demo funds to user balance.
        
        Steps:
        1. Validate amount
        2. Start database transaction
        3. Lock user profile (select_for_update)
        4. Update profile balance
        5. Create Transaction record
        6. Commit transaction
        
        Args:
            user: User instance
            amount: Amount to deposit (uses DEMO_DEPOSIT_AMOUNT if None)
            description: Optional description
            
        Returns:
            Transaction instance
            
        Raises:
            ValidationError: Invalid amount
        """
        # Use demo amount if not specified
        if amount is None:
            amount = WalletService.DEMO_DEPOSIT_AMOUNT
        
        # Validate amount
        WalletService.validate_amount(amount, "пополнения")
        
        logger.info(f"Processing deposit for user {user.username}: {amount}")
        
        # Lock profile to prevent race conditions
        profile = Profile.objects.select_for_update().get(user=user)
        
        # Store balance before
        balance_before = profile.balance
        
        # Update balance
        profile.balance += amount
        profile.save()
        
        # Store balance after
        balance_after = profile.balance
        
        # Create transaction record
        txn = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or f'Демо-пополнение {amount} ₽',
            status=Transaction.TransactionStatus.COMPLETED
        )
        
        logger.info(
            f"Deposit completed for {user.username}: "
            f"{amount} (balance: {balance_before} -> {balance_after})"
        )
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def place_bet(user: User, amount: Decimal, description: str = '') -> Transaction:
        """
        Deduct bet amount from balance.
        
        Steps:
        1. Validate amount > 0
        2. Start database transaction
        3. Lock user profile
        4. Check sufficient balance
        5. Deduct from balance
        6. Create Transaction record
        7. Commit transaction
        
        Args:
            user: User instance
            amount: Bet amount
            description: Bet description (e.g., "Mines game bet")
            
        Returns:
            Transaction instance
            
        Raises:
            ValidationError: Invalid amount
            InsufficientFundsError: Balance < amount
        """
        # Validate amount
        WalletService.validate_amount(amount, "ставки")
        
        logger.info(f"Processing bet for user {user.username}: {amount}")
        
        # Lock profile to prevent race conditions
        profile = Profile.objects.select_for_update().get(user=user)
        
        # Store balance before
        balance_before = profile.balance
        
        # Check sufficient balance
        if balance_before < amount:
            logger.warning(
                f"Insufficient funds for {user.username}: "
                f"balance={balance_before}, required={amount}"
            )
            raise InsufficientFundsError(
                f"Недостаточно средств. Баланс: {balance_before} ₽, требуется: {amount} ₽"
            )
        
        # Deduct from balance
        profile.balance -= amount
        profile.total_wagered += amount
        profile.save()
        
        # Store balance after
        balance_after = profile.balance
        
        # Create transaction record
        txn = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=Transaction.TransactionType.BET,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or f'Ставка {amount} ₽',
            status=Transaction.TransactionStatus.COMPLETED
        )
        
        logger.info(
            f"Bet placed for {user.username}: "
            f"{amount} (balance: {balance_before} -> {balance_after})"
        )
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def add_winnings(user: User, amount: Decimal, description: str = '') -> Transaction:
        """
        Add winnings to balance.
        
        Steps:
        1. Validate amount >= 0
        2. Start database transaction
        3. Lock user profile
        4. Add to balance
        5. Create Transaction record
        6. Commit transaction
        
        Args:
            user: User instance
            amount: Winning amount
            description: Win description (e.g., "Mines game win 2.5x")
            
        Returns:
            Transaction instance
            
        Raises:
            ValidationError: Invalid amount
        """
        # Allow zero winnings (for games with 0x multiplier)
        if amount < 0:
            raise ValidationError("Сумма выигрыша не может быть отрицательной")
        
        # Skip transaction if amount is zero
        if amount == 0:
            logger.info(f"Skipping zero winnings for {user.username}")
            return None
        
        logger.info(f"Processing winnings for user {user.username}: {amount}")
        
        # Lock profile to prevent race conditions
        profile = Profile.objects.select_for_update().get(user=user)
        
        # Store balance before
        balance_before = profile.balance
        
        # Add to balance
        profile.balance += amount
        profile.total_won += amount
        profile.save()
        
        # Store balance after
        balance_after = profile.balance
        
        # Create transaction record
        txn = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=Transaction.TransactionType.WIN,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or f'Выигрыш {amount} ₽',
            status=Transaction.TransactionStatus.COMPLETED
        )
        
        logger.info(
            f"Winnings added for {user.username}: "
            f"{amount} (balance: {balance_before} -> {balance_after})"
        )
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def add_bonus(user: User, amount: Decimal, description: str = '') -> Transaction:
        """
        Add bonus to balance.
        
        Args:
            user: User instance
            amount: Bonus amount
            description: Bonus description
            
        Returns:
            Transaction instance
            
        Raises:
            ValidationError: Invalid amount
        """
        # Validate amount
        WalletService.validate_amount(amount, "бонуса")
        
        logger.info(f"Processing bonus for user {user.username}: {amount}")
        
        # Lock profile to prevent race conditions
        profile = Profile.objects.select_for_update().get(user=user)
        
        # Store balance before
        balance_before = profile.balance
        
        # Add to balance
        profile.balance += amount
        profile.save()
        
        # Store balance after
        balance_after = profile.balance
        
        # Create transaction record
        txn = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=Transaction.TransactionType.BONUS,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or f'Бонус {amount} ₽',
            status=Transaction.TransactionStatus.COMPLETED
        )
        
        logger.info(
            f"Bonus added for {user.username}: "
            f"{amount} (balance: {balance_before} -> {balance_after})"
        )
        
        return txn
    
    @staticmethod
    def get_transaction_history(
        user: User,
        limit: int = 50,
        transaction_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> QuerySet[Transaction]:
        """
        Get user transaction history.
        
        Args:
            user: User instance
            limit: Maximum number of transactions to return
            transaction_type: Filter by transaction type (optional)
            status: Filter by status (optional)
            
        Returns:
            QuerySet ordered by created_at descending
        """
        queryset = Transaction.objects.filter(user=user)
        
        # Apply filters
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        # Limit results
        queryset = queryset[:limit]
        
        logger.info(
            f"Retrieved {queryset.count()} transactions for {user.username} "
            f"(type={transaction_type}, status={status})"
        )
        
        return queryset
    
    @staticmethod
    def get_transaction_by_id(user: User, transaction_id: int) -> Optional[Transaction]:
        """
        Get specific transaction by ID.
        
        Args:
            user: User instance
            transaction_id: Transaction ID
            
        Returns:
            Transaction instance or None
        """
        try:
            return Transaction.objects.get(id=transaction_id, user=user)
        except Transaction.DoesNotExist:
            logger.warning(f"Transaction {transaction_id} not found for user {user.username}")
            return None
    
    @staticmethod
    def get_balance_summary(user: User) -> dict:
        """
        Get balance summary with statistics.
        
        Args:
            user: User instance
            
        Returns:
            Dictionary with balance and statistics
        """
        from django.db.models import Sum, Count
        
        profile = user.profile
        
        # Get transaction statistics
        stats = Transaction.objects.filter(
            user=user,
            status=Transaction.TransactionStatus.COMPLETED
        ).aggregate(
            total_deposits=Sum(
                'amount',
                filter=models.Q(transaction_type=Transaction.TransactionType.DEPOSIT)
            ),
            total_bets=Sum(
                'amount',
                filter=models.Q(transaction_type=Transaction.TransactionType.BET)
            ),
            total_wins=Sum(
                'amount',
                filter=models.Q(transaction_type=Transaction.TransactionType.WIN)
            ),
            total_bonuses=Sum(
                'amount',
                filter=models.Q(transaction_type=Transaction.TransactionType.BONUS)
            ),
            transaction_count=Count('id')
        )
        
        # Calculate net profit/loss
        total_bets = stats['total_bets'] or Decimal('0')
        total_wins = stats['total_wins'] or Decimal('0')
        net_profit = total_wins - total_bets
        
        return {
            'balance': float(profile.balance),
            'total_wagered': float(profile.total_wagered),
            'total_won': float(profile.total_won),
            'total_deposits': float(stats['total_deposits'] or Decimal('0')),
            'total_bonuses': float(stats['total_bonuses'] or Decimal('0')),
            'net_profit': float(net_profit),
            'transaction_count': stats['transaction_count']
        }
