# Design Document: Crash Game

## Overview

The Crash Game is a real-time multiplayer betting game where players place bets and must cash out before a randomly generated crash point. The game features:

- **Real-time multiplier growth**: Starting at 1.00x and growing continuously
- **Provably fair mechanics**: Cryptographic verification of crash points
- **Multiple betting strategies**: Manual cashout, auto-cashout, multiple bets per round
- **Dramatic user experience**: Animations, sounds, and visual effects
- **Target RTP**: 97% (3% house edge)

The implementation follows the existing architecture patterns established in the codebase (Mines, Plinko, Dice, Slots games) and integrates with the existing WalletService and ProvablyFairService.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Graph      │  │   Controls   │  │   History    │      │
│  │  Animation   │  │  (Bet/Cash)  │  │   Display    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                    AJAX Polling (100ms)                      │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────┐
│                         Backend                              │
│                            │                                 │
│  ┌─────────────────────────▼──────────────────────────┐     │
│  │              CrashViews (API Layer)                 │     │
│  │  - GET /current/  - POST /bet/  - POST /cashout/   │     │
│  └─────────────────────────┬──────────────────────────┘     │
│                            │                                 │
│  ┌─────────────────────────▼──────────────────────────┐     │
│  │           CrashGameService (Business Logic)         │     │
│  │  - Round management  - Bet processing               │     │
│  │  - Multiplier calculation  - Cashout handling       │     │
│  └──┬──────────────┬──────────────┬───────────────────┘     │
│     │              │              │                          │
│     ▼              ▼              ▼                          │
│  ┌──────┐   ┌──────────┐   ┌──────────────┐                │
│  │Models│   │  Wallet  │   │  Provably    │                │
│  │      │   │ Service  │   │Fair Service  │                │
│  └──────┘   └──────────┘   └──────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Round Lifecycle

```
┌──────────┐
│ WAITING  │ (5-10 seconds countdown)
└────┬─────┘
     │ start_new_round()
     ▼
┌──────────┐
│  ACTIVE  │ (multiplier grows from 1.00x)
└────┬─────┘
     │ multiplier reaches crash_point
     ▼
┌──────────┐
│ CRASHED  │ (process all bets)
└────┬─────┘
     │ after processing
     ▼
┌──────────┐
│ WAITING  │ (new round)
└──────────┘
```

## Components and Interfaces

### 1. Data Models

#### CrashRound Model

```python
class CrashRound(models.Model):
    """
    Represents a single crash game round.
    """
    class RoundStatus(models.TextChoices):
        WAITING = 'waiting', 'Waiting'
        ACTIVE = 'active', 'Active'
        CRASHED = 'crashed', 'Crashed'
    
    # Round identification
    round_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    
    # Round state
    status = models.CharField(
        max_length=20,
        choices=RoundStatus.choices,
        default=RoundStatus.WAITING
    )
    
    # Crash point (predetermined)
    crash_point = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )
    
    # Provably fair fields
    server_seed = models.CharField(max_length=64)
    client_seed = models.CharField(max_length=64)
    server_seed_hash = models.CharField(max_length=64)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    crashed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    next_round_at = models.DateTimeField(null=True, blank=True)
```

#### CrashBet Model

```python
class CrashBet(models.Model):
    """
    Represents a player's bet in a crash round.
    """
    class BetStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CASHED_OUT = 'cashed_out', 'Cashed Out'
        LOST = 'lost', 'Lost'
    
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    round = models.ForeignKey(CrashRound, on_delete=models.CASCADE)
    
    # Bet details
    bet_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Cashout details
    cashout_multiplier = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    win_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=BetStatus.choices,
        default=BetStatus.ACTIVE
    )
    
    # Auto cashout
    auto_cashout_target = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('1.01'))]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    cashed_out_at = models.DateTimeField(null=True, blank=True)
```

### 2. CrashGameService

The service layer handles all business logic for the crash game.

#### Core Methods

```python
class CrashGameService:
    """
    Service for crash game business logic.
    """
    
    # Constants
    HOUSE_EDGE = Decimal('3.00')  # 3% house edge
    MIN_BET = Decimal('0.01')
    MAX_BET = Decimal('1000.00')
    MIN_CRASH_POINT = Decimal('1.00')
    MAX_CRASH_POINT = Decimal('10000.00')
    WAITING_DURATION = 8  # seconds between rounds
    MAX_BETS_PER_USER = 5
    MULTIPLIER_GROWTH_RATE = Decimal('0.01')  # per 100ms
    
    @staticmethod
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
        pass
    
    @staticmethod
    def activate_round(round: CrashRound) -> None:
        """
        Activate a waiting round.
        
        Steps:
        1. Update status to ACTIVE
        2. Set started_at timestamp
        3. Save round
        """
        pass
    
    @staticmethod
    def get_current_round() -> Optional[CrashRound]:
        """
        Get the current active or waiting round.
        
        Returns:
            CrashRound instance or None
        """
        pass
    
    @staticmethod
    def get_current_multiplier(round: CrashRound) -> Decimal:
        """
        Calculate current multiplier based on elapsed time.
        
        Formula:
        - elapsed_ms = (now - started_at) in milliseconds
        - multiplier = 1.00 + (elapsed_ms / 100) * MULTIPLIER_GROWTH_RATE
        - capped at crash_point
        
        Args:
            round: Active CrashRound
            
        Returns:
            Current multiplier (1.00x to crash_point)
        """
        pass
    
    @staticmethod
    @transaction.atomic
    def place_bet(
        user: User,
        amount: Decimal,
        auto_cashout_target: Optional[Decimal] = None
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
        pass
    
    @staticmethod
    @transaction.atomic
    def cashout(user: User, bet_id: int) -> CrashBet:
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
        pass
    
    @staticmethod
    def process_auto_cashouts(round: CrashRound, current_multiplier: Decimal) -> int:
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
            round: Current CrashRound
            current_multiplier: Current multiplier
            
        Returns:
            Number of bets cashed out
        """
        pass
    
    @staticmethod
    @transaction.atomic
    def crash_round(round: CrashRound) -> None:
        """
        Crash the current round and process all bets.
        
        Steps:
        1. Update round status to CRASHED
        2. Set crashed_at timestamp
        3. Get all ACTIVE bets for this round
        4. Update all active bets to status=LOST
        5. Save round
        
        Args:
            round: CrashRound to crash
        """
        pass
    
    @staticmethod
    def get_round_history(limit: int = 50) -> QuerySet[CrashRound]:
        """
        Get history of completed rounds.
        
        Args:
            limit: Maximum number of rounds to return
            
        Returns:
            QuerySet of CrashRound ordered by created_at descending
        """
        pass
    
    @staticmethod
    def get_user_bets(user: User, round: CrashRound) -> QuerySet[CrashBet]:
        """
        Get user's bets for a specific round.
        
        Args:
            user: User instance
            round: CrashRound instance
            
        Returns:
            QuerySet of CrashBet
        """
        pass
    
    @staticmethod
    def calculate_crash_point(server_seed: str, client_seed: str) -> Decimal:
        """
        Calculate crash point using provably fair algorithm.
        
        Formula:
        - random_value = HMAC-SHA256(server_seed, client_seed) -> [0, 1]
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
        pass
```

### 3. API Endpoints

#### GET /api/games/crash/current/

Get current round information and multiplier.

**Response (WAITING):**
```json
{
  "round_id": "uuid",
  "status": "waiting",
  "next_round_at": "2024-01-01T12:00:00Z",
  "seconds_until_start": 5
}
```

**Response (ACTIVE):**
```json
{
  "round_id": "uuid",
  "status": "active",
  "current_multiplier": "2.45",
  "started_at": "2024-01-01T12:00:00Z",
  "user_bets": [
    {
      "id": 123,
      "bet_amount": "10.00",
      "potential_win": "24.50",
      "auto_cashout_target": "5.00",
      "status": "active"
    }
  ]
}
```

**Response (CRASHED):**
```json
{
  "round_id": "uuid",
  "status": "crashed",
  "crash_point": "3.67",
  "crashed_at": "2024-01-01T12:00:05Z",
  "next_round_at": "2024-01-01T12:00:13Z"
}
```

#### POST /api/games/crash/bet/

Place a bet in the current round.

**Request:**
```json
{
  "amount": "10.00",
  "auto_cashout_target": "2.00"  // optional
}
```

**Response:**
```json
{
  "bet_id": 123,
  "round_id": "uuid",
  "bet_amount": "10.00",
  "auto_cashout_target": "2.00",
  "status": "active",
  "balance": "490.00"
}
```

#### POST /api/games/crash/cashout/

Cash out an active bet.

**Request:**
```json
{
  "bet_id": 123
}
```

**Response:**
```json
{
  "bet_id": 123,
  "cashout_multiplier": "2.45",
  "win_amount": "24.50",
  "status": "cashed_out",
  "balance": "514.50"
}
```

#### GET /api/games/crash/history/

Get history of recent rounds.

**Response:**
```json
{
  "rounds": [
    {
      "round_id": "uuid",
      "crash_point": "3.67",
      "crashed_at": "2024-01-01T12:00:05Z"
    },
    // ... up to 50 rounds
  ]
}
```

## Data Models

### Database Schema

```sql
-- CrashRound table
CREATE TABLE crash_round (
    id SERIAL PRIMARY KEY,
    round_id UUID UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL,
    crash_point DECIMAL(10, 2) NOT NULL,
    server_seed VARCHAR(64) NOT NULL,
    client_seed VARCHAR(64) NOT NULL,
    server_seed_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    crashed_at TIMESTAMP,
    next_round_at TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);

-- CrashBet table
CREATE TABLE crash_bet (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_user(id),
    round_id INTEGER NOT NULL REFERENCES crash_round(id),
    bet_amount DECIMAL(12, 2) NOT NULL,
    cashout_multiplier DECIMAL(10, 2),
    win_amount DECIMAL(12, 2) DEFAULT 0.00,
    status VARCHAR(20) NOT NULL,
    auto_cashout_target DECIMAL(10, 2),
    created_at TIMESTAMP NOT NULL,
    cashed_out_at TIMESTAMP,
    INDEX idx_user_round (user_id, round_id),
    INDEX idx_round_status (round_id, status),
    INDEX idx_auto_cashout (round_id, status, auto_cashout_target)
);
```

### Model Relationships

- **CrashRound** has many **CrashBet** (one-to-many)
- **User** has many **CrashBet** (one-to-many)
- **CrashBet** belongs to **User** and **CrashRound**

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

