from django.db import models
from django.conf import settings
from decimal import Decimal

# Create your models here.

class Transaction(models.Model):
    """
    Record of financial operation.
    Tracks all balance changes with before/after snapshots.
    """
    
    class TransactionType(models.TextChoices):
        DEPOSIT = 'deposit', 'Депозит'
        BET = 'bet', 'Ставка'
        WIN = 'win', 'Выигрыш'
        BONUS = 'bonus', 'Бонус'
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', 'В обработке'
        COMPLETED = 'completed', 'Завершена'
        FAILED = 'failed', 'Ошибка'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Пользователь'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Сумма'
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        verbose_name='Тип транзакции'
    )
    balance_before = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Баланс до'
    )
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Баланс после'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.COMPLETED,
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='user_created_idx'),
            models.Index(fields=['transaction_type', 'status'], name='type_status_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount} ₽ - {self.user.username}"
    
    def get_amount_display(self):
        """Format amount with sign based on transaction type"""
        if self.transaction_type in [self.TransactionType.DEPOSIT, self.TransactionType.WIN, self.TransactionType.BONUS]:
            return f"+{self.amount}"
        else:  # BET
            return f"-{self.amount}"
    
    @property
    def is_completed(self):
        """Check if transaction is completed"""
        return self.status == self.TransactionStatus.COMPLETED
    
    @property
    def is_pending(self):
        """Check if transaction is pending"""
        return self.status == self.TransactionStatus.PENDING
    
    @property
    def is_failed(self):
        """Check if transaction is failed"""
        return self.status == self.TransactionStatus.FAILED
