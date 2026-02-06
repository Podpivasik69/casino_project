# Design Document: Online Casino MVP

## Overview

Данный документ описывает архитектуру и дизайн MVP онлайн-казино на Django с двумя играми (Mines и Plinko). Система построена на принципах SOLID и использует сервисный слой для разделения бизнес-логики от представления.

### Key Design Principles

- **Service Layer Pattern**: Вся бизнес-логика инкапсулирована в сервисах
- **Single Responsibility Principle**: Каждый компонент имеет одну четко определенную ответственность
- **Dependency Injection**: Сервисы получают зависимости через конструктор
- **Atomic Transactions**: Все операции с балансом выполняются атомарно
- **Provably Fair**: Криптографическая проверяемость результатов игр

### Technology Stack

- **Backend**: Django 4.x
- **Database**: SQLite (для MVP)
- **Authentication**: Django built-in auth system
- **API**: Django REST Framework (опционально) или Django views с JSON responses
- **Frontend**: Django templates + vanilla JavaScript
- **Cryptography**: Python hashlib (HMAC-SHA256)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Presentation Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Templates  │  │  API Views   │  │  Static JS   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        Service Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │WalletService │  │MinesService  │  │PlinkoService │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  AuthService │  │ProvablyFair  │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         Data Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  User Model  │  │Profile Model │  │Transaction   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  MinesGame   │  │  PlinkoGame  │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Application Structure

```
casino/                      # Django project
├── settings.py             # Configuration
├── urls.py                 # Root URL routing
└── wsgi.py                 # WSGI entry point

users/                      # User management app
├── models.py              # User, Profile models
├── services.py            # AuthService
├── views.py               # Auth views
├── urls.py                # Auth URLs
└── templates/             # Auth templates

wallet/                     # Wallet management app
├── models.py              # Transaction model
├── services.py            # WalletService
├── views.py               # Wallet views
└── urls.py                # Wallet URLs

games/                      # Games app
├── models.py              # MinesGame, PlinkoGame models
├── services/
│   ├── mines_service.py   # MinesGameService
│   ├── plinko_service.py  # PlinkoGameService
│   └── provably_fair.py   # ProvablyFairService
├── views.py               # Game views
├── urls.py                # Game URLs
└── templates/             # Game templates
```

## Components and Interfaces

### 1. User Management Components

#### User Model (Extended AbstractUser)

```python
class User(AbstractUser):
    """
    Extended Django user model.
    Uses Django's built-in authentication.
    """
    email: EmailField (unique=True, required=True)
    username: CharField (unique=True, max_length=150)
    date_joined: DateTimeField (auto_now_add=True)
    
    # Inherited from AbstractUser:
    # - password (hashed)
    # - is_active
    # - is_staff
    # - is_superuser
```

#### Profile Model

```python
class Profile(Model):
    """
    User profile with demo balance.
    One-to-one relationship with User.
    """
    user: OneToOneField(User, on_delete=CASCADE)
    balance: DecimalField (max_digits=12, decimal_places=2, default=0)
    created_at: DateTimeField (auto_now_add=True)
    updated_at: DateTimeField (auto_now=True)
    
    constraints:
        - balance >= 0 (CheckConstraint)
```

#### AuthService

```python
class AuthService:
    """
    Service for user authentication operations.
    """
    
    def register_user(username: str, email: str, password: str) -> User:
        """
        Register new user with profile.
        
        Steps:
        1. Validate input data
        2. Check username/email uniqueness
        3. Create User with hashed password
        4. Create Profile with initial balance
        5. Return User instance
        
        Raises:
            ValidationError: Invalid input data
            IntegrityError: Username/email already exists
        """
    
    def authenticate_user(username: str, password: str) -> User | None:
        """
        Authenticate user credentials.
        
        Returns:
            User instance if valid, None otherwise
        """
    
    def logout_user(request) -> None:
        """
        Logout user and clear session.
        """
```

### 2. Wallet Components

#### Transaction Model

```python
class Transaction(Model):
    """
    Record of financial operation.
    """
    class TransactionType(TextChoices):
        DEPOSIT = 'deposit'
        BET = 'bet'
        WIN = 'win'
    
    user: ForeignKey(User, on_delete=CASCADE)
    amount: DecimalField (max_digits=12, decimal_places=2)
    transaction_type: CharField (choices=TransactionType)
    balance_after: DecimalField (max_digits=12, decimal_places=2)
    description: TextField (blank=True)
    created_at: DateTimeField (auto_now_add=True)
    
    indexes:
        - user, created_at (for history queries)
```

#### WalletService

```python
class WalletService:
    """
    Service for wallet operations.
    All methods use database transactions for atomicity.
    """
    
    def get_balance(user: User) -> Decimal:
        """
        Get current user balance.
        
        Returns:
            Current balance from Profile
        """
    
    def deposit(user: User, amount: Decimal) -> Transaction:
        """
        Add demo funds to user balance.
        
        Steps:
        1. Validate amount > 0
        2. Start database transaction
        3. Lock user profile (select_for_update)
        4. Update profile balance
        5. Create Transaction record
        6. Commit transaction
        
        Returns:
            Transaction instance
            
        Raises:
            ValidationError: Invalid amount
        """
    
    def place_bet(user: User, amount: Decimal, description: str) -> Transaction:
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
        
        Returns:
            Transaction instance
            
        Raises:
            ValidationError: Invalid amount
            InsufficientFundsError: Balance < amount
        """
    
    def add_winnings(user: User, amount: Decimal, description: str) -> Transaction:
        """
        Add winnings to balance.
        
        Steps:
        1. Validate amount >= 0
        2. Start database transaction
        3. Lock user profile
        4. Add to balance
        5. Create Transaction record
        6. Commit transaction
        
        Returns:
            Transaction instance
        """
    
    def get_transaction_history(user: User, limit: int = 50) -> QuerySet[Transaction]:
        """
        Get user transaction history.
        
        Returns:
            QuerySet ordered by created_at descending
        """
```

### 3. Mines Game Components

#### MinesGame Model

```python
class MinesGame(Model):
    """
    Mines game instance.
    """
    class GameState(TextChoices):
        ACTIVE = 'active'
        WON = 'won'
        LOST = 'lost'
        CASHED_OUT = 'cashed_out'
    
    user: ForeignKey(User, on_delete=CASCADE)
    bet_amount: DecimalField (max_digits=12, decimal_places=2)
    mine_count: IntegerField (validators=[MinValueValidator(3), MaxValueValidator(20)])
    
    # Game state
    state: CharField (choices=GameState, default=ACTIVE)
    opened_cells: JSONField (default=list)  # List of (row, col) tuples
    current_multiplier: DecimalField (max_digits=8, decimal_places=2, default=1.0)
    
    # Provably Fair
    server_seed: CharField (max_length=64)
    client_seed: CharField (max_length=64)
    nonce: IntegerField (default=0)
    server_seed_hash: CharField (max_length=64)  # SHA256 hash, revealed before game
    mine_positions: JSONField (null=True, blank=True)  # Revealed after game ends
    
    # Timestamps
    created_at: DateTimeField (auto_now_add=True)
    ended_at: DateTimeField (null=True, blank=True)
    
    indexes:
        - user, created_at
        - state
```

#### MinesGameService

```python
class MinesGameService:
    """
    Service for Mines game logic.
    """
    
    def __init__(self, wallet_service: WalletService, provably_fair: ProvablyFairService):
        self.wallet_service = wallet_service
        self.provably_fair = provably_fair
    
    def create_game(user: User, bet_amount: Decimal, mine_count: int, 
                   client_seed: str = None) -> MinesGame:
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
        
        Returns:
            MinesGame instance with state=ACTIVE
            
        Raises:
            ValidationError: Invalid parameters
            InsufficientFundsError: Not enough balance
        """
    
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
        
        Returns:
            {
                'is_mine': bool,
                'multiplier': Decimal,
                'game_state': str,
                'mine_positions': list (if game ended)
            }
            
        Raises:
            ValidationError: Invalid operation
        """
    
    def cashout(game: MinesGame) -> Decimal:
        """
        Cash out current winnings.
        
        Steps:
        1. Validate game is ACTIVE
        2. Calculate winnings = bet_amount * current_multiplier
        3. Add winnings via WalletService
        4. Set state=CASHED_OUT
        5. Set ended_at timestamp
        6. Reveal mine positions
        7. Return winnings amount
        
        Returns:
            Winnings amount
            
        Raises:
            ValidationError: Game not active
        """
    
    def get_verification_data(game: MinesGame) -> dict:
        """
        Get provably fair verification data.
        
        Returns:
            {
                'server_seed': str,
                'client_seed': str,
                'nonce': int,
                'mine_positions': list
            }
        """
    
    def calculate_multiplier(mine_count: int, opened_safe_cells: int) -> Decimal:
        """
        Calculate current multiplier based on mines and opened cells.
        
        Formula:
        multiplier = product of (25 - i) / (25 - mine_count - i) for i in range(opened_safe_cells)
        
        Max multiplier: 504x (when mine_count=20, opened=4)
        """
```

### 4. Plinko Game Components

#### PlinkoGame Model

```python
class PlinkoGame(Model):
    """
    Plinko game instance.
    """
    class RiskLevel(TextChoices):
        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'
    
    user: ForeignKey(User, on_delete=CASCADE)
    bet_amount: DecimalField (max_digits=12, decimal_places=2)
    row_count: IntegerField (validators=[MinValueValidator(12), MaxValueValidator(16)])
    risk_level: CharField (choices=RiskLevel)
    
    # Result
    final_multiplier: DecimalField (max_digits=8, decimal_places=2, null=True)
    ball_path: JSONField (null=True)  # List of 0/1 for left/right at each row
    bucket_index: IntegerField (null=True)
    
    # Timestamps
    created_at: DateTimeField (auto_now_add=True)
    
    indexes:
        - user, created_at
```

#### PlinkoGameService

```python
class PlinkoGameService:
    """
    Service for Plinko game logic.
    """
    
    # Multiplier configurations for each risk level and row count
    MULTIPLIERS = {
        'low': {
            12: [8.4, 4.2, 2.1, 1.4, 1.1, 1.0, 1.0, 1.1, 1.4, 2.1, 4.2, 8.4, 16.8],
            13: [13.0, 6.0, 3.0, 1.6, 1.2, 1.0, 1.0, 1.0, 1.2, 1.6, 3.0, 6.0, 13.0, 26.0],
            14: [18.0, 8.0, 4.0, 2.0, 1.4, 1.1, 1.0, 1.0, 1.1, 1.4, 2.0, 4.0, 8.0, 18.0, 36.0],
            15: [25.0, 11.0, 5.0, 2.5, 1.5, 1.2, 1.0, 1.0, 1.0, 1.2, 1.5, 2.5, 5.0, 11.0, 25.0, 50.0],
            16: [35.0, 15.0, 7.0, 3.0, 2.0, 1.3, 1.1, 1.0, 1.0, 1.1, 1.3, 2.0, 3.0, 7.0, 15.0, 35.0, 70.0]
        },
        'medium': {
            12: [13.0, 6.0, 3.0, 1.5, 1.0, 0.5, 0.3, 0.5, 1.0, 1.5, 3.0, 6.0, 13.0],
            13: [20.0, 9.0, 4.0, 2.0, 1.2, 0.6, 0.3, 0.3, 0.6, 1.2, 2.0, 4.0, 9.0, 20.0],
            14: [30.0, 13.0, 6.0, 3.0, 1.5, 0.8, 0.4, 0.4, 0.8, 1.5, 3.0, 6.0, 13.0, 30.0, 60.0],
            15: [43.0, 18.0, 8.0, 4.0, 2.0, 1.0, 0.5, 0.3, 0.5, 1.0, 2.0, 4.0, 8.0, 18.0, 43.0, 86.0],
            16: [60.0, 25.0, 11.0, 5.0, 2.5, 1.3, 0.6, 0.3, 0.3, 0.6, 1.3, 2.5, 5.0, 11.0, 25.0, 60.0, 120.0]
        },
        'high': {
            12: [29.0, 13.0, 5.0, 2.0, 0.7, 0.2, 0.1, 0.2, 0.7, 2.0, 5.0, 13.0, 29.0],
            13: [43.0, 18.0, 7.0, 2.5, 1.0, 0.3, 0.1, 0.1, 0.3, 1.0, 2.5, 7.0, 18.0, 43.0],
            14: [76.0, 29.0, 11.0, 4.0, 1.5, 0.5, 0.2, 0.2, 0.5, 1.5, 4.0, 11.0, 29.0, 76.0, 152.0],
            15: [120.0, 43.0, 15.0, 6.0, 2.0, 0.7, 0.2, 0.1, 0.2, 0.7, 2.0, 6.0, 15.0, 43.0, 120.0, 240.0],
            16: [170.0, 60.0, 21.0, 8.0, 3.0, 1.0, 0.3, 0.1, 0.1, 0.3, 1.0, 3.0, 8.0, 21.0, 60.0, 170.0, 555.0]
        }
    }
    
    def __init__(self, wallet_service: WalletService):
        self.wallet_service = wallet_service
    
    def create_game(user: User, bet_amount: Decimal, row_count: int, 
                   risk_level: str) -> PlinkoGame:
        """
        Create new Plinko game (doesn't drop ball yet).
        
        Steps:
        1. Validate parameters
        2. Create PlinkoGame instance
        3. Return game
        
        Note: Bet is placed when ball is dropped, not at game creation
        
        Returns:
            PlinkoGame instance
            
        Raises:
            ValidationError: Invalid parameters
        """
    
    def drop_ball(game: PlinkoGame) -> dict:
        """
        Drop ball and calculate result.
        
        Steps:
        1. Check user has sufficient balance
        2. Place bet via WalletService
        3. Simulate ball path (random walk)
        4. Determine final bucket
        5. Get multiplier for bucket
        6. Calculate winnings
        7. Add winnings via WalletService (if > 0)
        8. Update game with results
        9. Return result
        
        Returns:
            {
                'ball_path': list[int],
                'bucket_index': int,
                'multiplier': Decimal,
                'winnings': Decimal
            }
            
        Raises:
            InsufficientFundsError: Not enough balance
        """
    
    def simulate_ball_path(row_count: int) -> tuple[list[int], int]:
        """
        Simulate ball dropping through rows.
        
        Uses random walk: at each row, 50% chance to go left (0) or right (1).
        Final bucket index = sum of path (number of rights).
        
        Returns:
            (path, bucket_index)
            path: list of 0/1 for each row
            bucket_index: 0 to row_count (inclusive)
        """
    
    def get_multiplier(risk_level: str, row_count: int, bucket_index: int) -> Decimal:
        """
        Get multiplier for specific bucket.
        
        Returns:
            Multiplier from MULTIPLIERS configuration
        """
    
    def auto_play(user: User, bet_amount: Decimal, row_count: int, 
                 risk_level: str, drop_count: int) -> list[dict]:
        """
        Execute multiple drops automatically.
        
        Steps:
        1. Validate parameters
        2. For each drop (up to drop_count):
            a. Check sufficient balance
            b. Create game
            c. Drop ball
            d. Collect result
            e. If insufficient balance, stop
        3. Return all results
        
        Returns:
            List of drop results
            
        Raises:
            ValidationError: Invalid parameters
        """
```

### 5. Provably Fair Service

#### ProvablyFairService

```python
class ProvablyFairService:
    """
    Service for provably fair game outcome generation.
    Uses HMAC-SHA256 for cryptographic verification.
    """
    
    def generate_server_seed() -> str:
        """
        Generate cryptographically secure server seed.
        
        Returns:
            64-character hex string
        """
    
    def generate_client_seed() -> str:
        """
        Generate default client seed.
        
        Returns:
            64-character hex string
        """
    
    def hash_seed(seed: str) -> str:
        """
        Create SHA256 hash of seed.
        
        Returns:
            64-character hex string
        """
    
    def generate_mine_positions(server_seed: str, client_seed: str, 
                               nonce: int, mine_count: int) -> list[tuple[int, int]]:
        """
        Generate mine positions using provably fair algorithm.
        
        Algorithm:
        1. Combine server_seed + client_seed + nonce
        2. Create HMAC-SHA256 hash
        3. Use hash bytes to generate random positions
        4. Use Fisher-Yates shuffle with hash as seed
        5. Select first mine_count positions
        
        Returns:
            List of (row, col) tuples for mine positions
        """
    
    def verify_mine_positions(server_seed: str, client_seed: str, 
                             nonce: int, mine_count: int, 
                             claimed_positions: list[tuple[int, int]]) -> bool:
        """
        Verify that mine positions match the seeds.
        
        Returns:
            True if positions match, False otherwise
        """
```

## Data Models

### Entity Relationship Diagram

```
┌─────────────┐
│    User     │
│ (Django)    │
└──────┬──────┘
       │ 1:1
       ▼
┌─────────────┐
│   Profile   │
│  - balance  │
└──────┬──────┘
       │ 1:N
       ├──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Transaction  │ │  MinesGame  │ │ PlinkoGame  │ │   (other)   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### Database Indexes

**Profile**:
- PRIMARY KEY: id
- UNIQUE: user_id

**Transaction**:
- PRIMARY KEY: id
- INDEX: (user_id, created_at) - for transaction history queries
- FOREIGN KEY: user_id -> User.id

**MinesGame**:
- PRIMARY KEY: id
- INDEX: (user_id, created_at) - for game history
- INDEX: state - for active games queries
- FOREIGN KEY: user_id -> User.id

**PlinkoGame**:
- PRIMARY KEY: id
- INDEX: (user_id, created_at) - for game history
- FOREIGN KEY: user_id -> User.id

### Data Validation Rules

1. **Balance**: Must be >= 0 (enforced by database constraint)
2. **Bet Amount**: Must be > 0 and <= user balance
3. **Mine Count**: Must be 3-20 (inclusive)
4. **Row Count**: Must be 12-16 (inclusive)
5. **Risk Level**: Must be one of: low, medium, high
6. **Cell Coordinates**: Must be 0-4 for both row and col
7. **Transaction Amount**: Must be > 0 for deposits and bets, >= 0 for wins

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

