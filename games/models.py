"""
Game models for Mines and Plinko.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class MinesGame(models.Model):
    """
    Mines game instance.
    
    Game flow:
    1. User creates game with bet_amount and mine_count
    2. Server generates provably fair mine positions
    3. User opens cells one by one
    4. If mine hit: game ends (state=LOST)
    5. If safe: multiplier increases, user can continue or cashout
    6. On cashout: winnings added to balance (state=CASHED_OUT)
    """
    
    class GameState(models.TextChoices):
        ACTIVE = 'active', 'Активна'
        WON = 'won', 'Выиграна'
        LOST = 'lost', 'Проиграна'
        CASHED_OUT = 'cashed_out', 'Забрана'
    
    # User and bet
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mines_games',
        verbose_name='Пользователь'
    )
    bet_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Сумма ставки'
    )
    mine_count = models.IntegerField(
        validators=[MinValueValidator(3), MaxValueValidator(20)],
        verbose_name='Количество мин'
    )
    
    # Game state
    state = models.CharField(
        max_length=20,
        choices=GameState.choices,
        default=GameState.ACTIVE,
        verbose_name='Состояние игры'
    )
    opened_cells = models.JSONField(
        default=list,
        verbose_name='Открытые клетки',
        help_text='Список [row, col] открытых клеток'
    )
    current_multiplier = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1.0,
        verbose_name='Текущий множитель'
    )
    
    # Provably Fair fields
    server_seed = models.CharField(
        max_length=64,
        verbose_name='Server seed',
        help_text='Секретный seed сервера (64 hex chars)'
    )
    client_seed = models.CharField(
        max_length=64,
        verbose_name='Client seed',
        help_text='Публичный seed клиента (64 hex chars)'
    )
    nonce = models.IntegerField(
        default=0,
        verbose_name='Nonce',
        help_text='Номер раунда для данной пары seeds'
    )
    server_seed_hash = models.CharField(
        max_length=64,
        verbose_name='Server seed hash',
        help_text='SHA256 хэш server_seed (показывается до игры)'
    )
    mine_positions = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Позиции мин',
        help_text='Список [row, col] позиций мин (раскрывается после игры)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создана'
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Завершена'
    )
    
    class Meta:
        verbose_name = 'Игра Mines'
        verbose_name_plural = 'Игры Mines'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='mines_user_created_idx'),
            models.Index(fields=['state'], name='mines_state_idx'),
        ]
    
    def __str__(self):
        return f"Mines #{self.id} - {self.user.username} - {self.get_state_display()}"
    
    def is_active(self):
        """Check if game is active"""
        return self.state == self.GameState.ACTIVE
    
    def is_ended(self):
        """Check if game has ended"""
        return self.state in [self.GameState.WON, self.GameState.LOST, self.GameState.CASHED_OUT]
    
    def get_opened_cells_count(self):
        """Get number of opened cells"""
        return len(self.opened_cells)
    
    def is_cell_opened(self, row, col):
        """Check if cell is already opened"""
        return [row, col] in self.opened_cells
    
    def get_safe_cells_count(self):
        """Get number of safe cells (total - mines)"""
        return 25 - self.mine_count
    
    def can_cashout(self):
        """Check if user can cashout (has opened at least one cell)"""
        return self.is_active() and self.get_opened_cells_count() > 0


class PlinkoGame(models.Model):
    """
    Plinko game instance.
    
    Game flow:
    1. User creates game with bet_amount, row_count, and risk_level
    2. Ball is dropped and simulates random walk through rows
    3. Ball lands in bucket with specific multiplier
    4. Winnings calculated and added to balance
    """
    
    class RiskLevel(models.TextChoices):
        LOW = 'low', 'Низкий'
        MEDIUM = 'medium', 'Средний'
        HIGH = 'high', 'Высокий'
    
    # User and bet
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='plinko_games',
        verbose_name='Пользователь'
    )
    bet_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Сумма ставки'
    )
    row_count = models.IntegerField(
        verbose_name='Количество рядов',
        help_text='Допустимые значения: 5, 9, 11, 13, 15'
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        verbose_name='Уровень риска'
    )
    
    # Result
    final_multiplier = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Финальный множитель'
    )
    ball_path = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Путь шарика',
        help_text='Список 0/1 для left/right на каждом ряду'
    )
    bucket_index = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Индекс корзины',
        help_text='Финальная корзина (0 to row_count)'
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создана'
    )
    
    class Meta:
        verbose_name = 'Игра Plinko'
        verbose_name_plural = 'Игры Plinko'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='plinko_user_created_idx'),
        ]
    
    def __str__(self):
        return f"Plinko #{self.id} - {self.user.username} - {self.get_risk_level_display()}"
    
    def is_completed(self):
        """Check if game is completed (ball dropped)"""
        return self.final_multiplier is not None


class DiceGame(models.Model):
    """
    Dice game instance.
    
    Game flow:
    1. User creates game with bet_amount and selected_number (1-6)
    2. Server generates provably fair random number (1-6)
    3. If match: user wins 6x multiplier
    4. If no match: user loses bet
    """
    
    # User and bet
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dice_games',
        verbose_name='Пользователь'
    )
    bet_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Сумма ставки'
    )
    selected_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        verbose_name='Выбранное число'
    )
    
    # Result
    rolled_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        verbose_name='Выпавшее число'
    )
    multiplier = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Множитель'
    )
    won = models.BooleanField(
        default=False,
        verbose_name='Выиграл'
    )
    
    # Provably Fair fields
    server_seed = models.CharField(
        max_length=64,
        verbose_name='Server seed',
        help_text='Секретный seed сервера (64 hex chars)'
    )
    client_seed = models.CharField(
        max_length=64,
        verbose_name='Client seed',
        help_text='Публичный seed клиента (64 hex chars)'
    )
    nonce = models.IntegerField(
        default=0,
        verbose_name='Nonce',
        help_text='Номер раунда для данной пары seeds'
    )
    server_seed_hash = models.CharField(
        max_length=64,
        verbose_name='Server seed hash',
        help_text='SHA256 хэш server_seed (показывается до игры)'
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создана'
    )
    
    class Meta:
        verbose_name = 'Игра Dice'
        verbose_name_plural = 'Игры Dice'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='dice_user_created_idx'),
        ]
    
    def __str__(self):
        return f"Dice #{self.id} - {self.user.username} - {'Выиграл' if self.won else 'Проиграл'}"


class SlotsGame(models.Model):
    """
    Slots game instance.
    
    Game flow:
    1. User creates game with bet_amount and reels_count (3 or 5)
    2. Server generates provably fair random symbols for reels
    3. System checks for winning combinations
    4. Winnings calculated and added to balance
    """
    
    REELS_CHOICES = [
        (3, '3 барабана'),
        (5, '5 барабанов')
    ]
    
    # User and bet
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='slots_games',
        verbose_name='Пользователь'
    )
    bet_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Сумма ставки'
    )
    
    # Game mode
    reels_count = models.IntegerField(
        choices=REELS_CHOICES,
        default=5,
        verbose_name='Количество барабанов'
    )
    
    # Game result
    reels = models.JSONField(
        verbose_name='Барабаны',
        help_text='Массив из 3 или 5 символов'
    )
    multiplier = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Множитель'
    )
    win_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Сумма выигрыша'
    )
    winning_combination = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Выигрышная комбинация'
    )
    
    # Provably Fair fields
    server_seed = models.CharField(
        max_length=64,
        verbose_name='Server seed',
        help_text='Секретный seed сервера (64 hex chars)'
    )
    client_seed = models.CharField(
        max_length=64,
        verbose_name='Client seed',
        help_text='Публичный seed клиента (64 hex chars)'
    )
    nonce = models.IntegerField(
        default=0,
        verbose_name='Nonce',
        help_text='Номер раунда для данной пары seeds'
    )
    server_seed_hash = models.CharField(
        max_length=64,
        verbose_name='Server seed hash',
        help_text='SHA256 хэш server_seed (показывается до игры)'
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создана'
    )
    
    class Meta:
        verbose_name = 'Игра Slots'
        verbose_name_plural = 'Игры Slots'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='slots_user_created_idx'),
        ]
    
    def __str__(self):
        return f"Slots #{self.id} - {self.user.username} - {self.reels_count} reels"
    
    def is_win(self):
        """Check if game is a win"""
        return self.multiplier > 0
    
    def get_win_amount(self):
        """Get win amount"""
        return self.win_amount
