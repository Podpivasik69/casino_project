# Design Document: Slots Game

## Overview

The Slots game is a dual-mode slot machine implementation for the Django casino platform with two gameplay options: a classic 3-reel mode for quick gameplay and an extended 5-reel mode with more winning combinations. Players place bets, choose their preferred mode, spin the reels to generate random symbols with stunning vertical scrolling animations, and win based on matching symbol combinations. The game follows the established patterns from Dice, Mines, and Plinko games, integrating with the existing Wallet Service and Provably Fair Service.

The game features advanced visual effects including vertical scrolling reels, bounce animations on stop, glowing winning lines, and jackpot explosion effects. The game supports both manual single spins and auto-spin functionality for continuous play. All game outcomes are verifiable through the Provably Fair system, ensuring transparency and trust.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ slots.html   │  │ slots.css    │  │ slots.js     │      │
│  │ (Template)   │  │ (Styling)    │  │ (Logic)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/JSON
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         games/views/slots_views.py                   │   │
│  │  - create_game()                                     │   │
│  │  - get_history()                                     │   │
│  │  - get_game()                                        │   │
│  │  - verify_game()                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      games/services/slots_service.py                 │   │
│  │  - create_and_play_game()                            │   │
│  │  - generate_reels()                                  │   │
│  │  - check_win()                                       │   │
│  │  - calculate_payout()                                │   │
│  │  - get_user_games()                                  │   │
│  │  - verify_game()                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Wallet Service         │  │  Provably Fair Service   │
│  - place_bet()           │  │  - generate_server_seed()│
│  - add_winnings()        │  │  - generate_client_seed()│
│  - check_balance()       │  │  - hash_seed()           │
└──────────────────────────┘  │  - generate_slots_reels()│
                              └──────────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────────┐
                              │    Database Layer        │
                              │  - SlotsGame model       │
                              │  - User model            │
                              │  - Transaction model     │
                              └──────────────────────────┘
```

### Data Flow

1. **Game Creation Flow**:
   - User submits bet amount via frontend
   - API validates authentication and request
   - Service validates bet amount and user balance
   - Wallet Service deducts bet amount
   - Provably Fair Service generates seeds and random symbols
   - Service checks for winning combinations
   - Service calculates payout
   - Wallet Service adds winnings (if any)
   - Game record saved to database
   - Response returned to frontend with results

2. **Auto-Spin Flow**:
   - Frontend initiates auto-spin with bet amount
   - Frontend repeatedly calls create_game API
   - Each spin follows standard game creation flow
   - Frontend stops on user action or insufficient balance error

## Components and Interfaces

### 1. SlotsGame Model

**Location**: `games/models.py`

**Fields**:
```python
class SlotsGame(models.Model):
    # User and bet
    user = ForeignKey(User)
    bet_amount = DecimalField(max_digits=12, decimal_places=2)
    
    # Game mode
    reels_count = IntegerField(choices=[(3, '3 Reels'), (5, '5 Reels')], default=5)
    
    # Game result
    reels = JSONField()  # Array of 3 or 5 symbols: ["🍒", "🍋", "🍊"]
    multiplier = DecimalField(max_digits=8, decimal_places=2)
    win_amount = DecimalField(max_digits=12, decimal_places=2, default=0)
    winning_combination = CharField(max_length=100, blank=True)
    
    # Provably Fair
    server_seed = CharField(max_length=64)
    client_seed = CharField(max_length=64)
    nonce = IntegerField(default=0)
    server_seed_hash = CharField(max_length=64)
    
    # Timestamp
    created_at = DateTimeField(auto_now_add=True)
```

**Methods**:
- `__str__()`: String representation
- `is_win()`: Returns True if multiplier > 0
- `get_win_amount()`: Returns calculated win amount

### 2. SlotsGameService

**Location**: `games/services/slots_service.py`

**Constants**:
```python
MIN_BET = Decimal('0.01')
MAX_BET = Decimal('10000.00')
SYMBOLS = ['🍒', '🍋', '🍊', '⭐', '🔔', '7️⃣']

# Win multipliers for 3-reel mode (all 3 matching)
MULTIPLIERS_3_REEL = {
    '7️⃣': Decimal('50.00'),
    '⭐': Decimal('25.00'),
    '🔔': Decimal('15.00'),
    '🍊': Decimal('10.00'),
    '🍋': Decimal('7.00'),
    '🍒': Decimal('5.00')
}

# Win multipliers for 5-reel mode (5-of-a-kind)
MULTIPLIERS_5X = {
    '7️⃣': Decimal('100.00'),
    '⭐': Decimal('50.00'),
    '🔔': Decimal('25.00'),
    '🍊': Decimal('15.00'),
    '🍋': Decimal('10.00'),
    '🍒': Decimal('5.00')
}

# Win multipliers for 5-reel mode (3-consecutive)
MULTIPLIERS_3X = {
    '7️⃣': Decimal('20.00'),
    '⭐': Decimal('10.00'),
    '🔔': Decimal('5.00')
}
```

**Methods**:

```python
@classmethod
def validate_bet(cls, bet_amount: Decimal) -> None:
    """
    Validate bet amount is within allowed range.
    
    Args:
        bet_amount: Bet amount to validate
        
    Raises:
        ValueError: If bet is invalid
    """

@classmethod
@transaction.atomic
def create_and_play_game(
    cls,
    user,
    bet_amount: Decimal,
    reels_count: int = 5,
    client_seed: str = None
) -> SlotsGame:
    """
    Create and play a slots game.
    
    Args:
        user: User playing the game
        bet_amount: Amount to bet
        reels_count: Number of reels (3 or 5), defaults to 5
        client_seed: Optional client seed for provably fair
        
    Returns:
        SlotsGame instance with results
        
    Raises:
        ValueError: If validation fails
        InsufficientFundsError: If balance too low
    """

@classmethod
def generate_reels(
    cls,
    server_seed: str,
    client_seed: str,
    nonce: int,
    reels_count: int = 5
) -> list:
    """
    Generate 3 or 5 random symbols using Provably Fair.
    
    Args:
        server_seed: Server seed for randomness
        client_seed: Client seed for randomness
        nonce: Nonce for this game
        reels_count: Number of reels (3 or 5)
        
    Returns:
        List of 3 or 5 symbols
    """

@classmethod
def check_win(cls, reels: list, reels_count: int) -> tuple:
    """
    Check for winning combinations in reels.
    
    Args:
        reels: List of 3 or 5 symbols
        reels_count: Number of reels (3 or 5)
        
    Returns:
        Tuple of (multiplier, winning_combination_description)
    """

@classmethod
def calculate_payout(cls, bet_amount: Decimal, multiplier: Decimal) -> Decimal:
    """
    Calculate payout amount.
    
    Args:
        bet_amount: Original bet
        multiplier: Win multiplier
        
    Returns:
        Payout amount (bet_amount * multiplier)
    """

@classmethod
def get_user_games(cls, user, limit: int = 10):
    """
    Get user's recent slots games.
    
    Args:
        user: User to get games for
        limit: Maximum number of games
        
    Returns:
        QuerySet of SlotsGame instances
    """

@classmethod
def get_game_by_id(cls, game_id: int, user=None):
    """
    Get game by ID.
    
    Args:
        game_id: Game ID
        user: Optional user filter
        
    Returns:
        SlotsGame instance or None
    """

@classmethod
def verify_game(cls, game: SlotsGame) -> bool:
    """
    Verify game result using provably fair.
    
    Args:
        game: SlotsGame instance
        
    Returns:
        True if verification passes
    """
```

### 3. API Endpoints

**Location**: `games/views/slots_views.py`

**Endpoints**:

```python
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_game(request):
    """
    POST /api/games/slots/create/
    
    Request Body:
    {
        "bet_amount": "10.00",
        "reels_count": 5,
        "client_seed": "optional_seed"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "game_id": 123,
            "bet_amount": "10.00",
            "reels_count": 5,
            "reels": ["🍒", "🍋", "🍊", "⭐", "🔔"],
            "multiplier": "0.00",
            "win_amount": "0.00",
            "winning_combination": "",
            "balance": "90.00",
            "server_seed_hash": "abc123...",
            "client_seed": "def456...",
            "nonce": 0,
            "created_at": "2024-01-01T12:00:00Z"
        }
    }
    """

@require_http_methods(["GET"])
@login_required
def get_history(request):
    """
    GET /api/games/slots/history/?limit=10
    
    Response:
    {
        "success": true,
        "data": {
            "games": [
                {
                    "game_id": 123,
                    "bet_amount": "10.00",
                    "reels": ["🍒", "🍋", "🍊", "⭐", "🔔"],
                    "multiplier": "0.00",
                    "win_amount": "0.00",
                    "winning_combination": "",
                    "created_at": "2024-01-01T12:00:00Z"
                }
            ],
            "total": 1
        }
    }
    """

@require_http_methods(["GET"])
@login_required
def get_game(request, game_id):
    """
    GET /api/games/slots/<game_id>/
    
    Response:
    {
        "success": true,
        "data": {
            "game_id": 123,
            "bet_amount": "10.00",
            "reels": ["🍒", "🍋", "🍊", "⭐", "🔔"],
            "multiplier": "0.00",
            "win_amount": "0.00",
            "winning_combination": "",
            "server_seed": "abc123...",
            "server_seed_hash": "def456...",
            "client_seed": "ghi789...",
            "nonce": 0,
            "created_at": "2024-01-01T12:00:00Z"
        }
    }
    """

@csrf_exempt
@require_http_methods(["POST"])
def verify_game(request):
    """
    POST /api/games/slots/verify/
    
    Request Body:
    {
        "game_id": 123
    }
    
    Response:
    {
        "success": true,
        "data": {
            "game_id": 123,
            "is_valid": true,
            "message": "Игра прошла проверку"
        }
    }
    """
```

### 4. Frontend Components

**Template**: `templates/slots.html`

**Structure**:
- Extends `base.html`
- Mode selection buttons (3-reel / 5-reel)
- Dynamic reel display (3 or 5 reels based on mode)
- Vertical scrolling animation containers for each reel
- Bet amount selection buttons (1, 5, 10, 50, 100, custom)
- Spin button with loading state
- Auto-spin toggle button
- Balance display with animated updates
- Win/loss result display with explosion effects
- Winning combination highlight with glow
- Game history section

**JavaScript**: `static/js/games/slots.js`

**Functions**:
```javascript
// Initialize game
function initSlotsGame() { }

// Handle mode selection (3 or 5 reels)
function selectMode(reelsCount) { }

// Handle spin button click
function handleSpin() { }

// Handle auto-spin toggle
function handleAutoSpin() { }

// Call API to create game
async function createGame(betAmount, reelsCount) { }

// Animate vertical scrolling for all reels
function animateReels(reelsCount) { }

// Stop reels sequentially with stagger effect
function stopReels(reels, reelsCount) { }

// Apply bounce effect when reel stops
function applyBounceEffect(reelElement) { }

// Display win with glow effect
function displayWinningCombination(reels, winningCombination) { }

// Trigger jackpot explosion animation
function triggerJackpotAnimation() { }

// Animate number counting up
function animateWinAmount(amount) { }

// Display reel results
function displayReels(reels) { }

// Display win/loss result
function displayResult(data) { }

// Update balance display with animation
function updateBalance(balance) { }

// Load game history
async function loadHistory() { }
```

**CSS**: `static/css/games/slots.css`

**Styling**:
- Reel containers with overflow hidden for scrolling effect
- Symbol display with large emoji
- Vertical scroll animation keyframes
- Bounce animation keyframes
- Glow effect for winning symbols (box-shadow, animation)
- Explosion/burst effect for jackpots (particles, scale)
- Smooth transitions for all state changes
- Responsive layout for 3 and 5 reel modes
- Button states (active, disabled, spinning)
- Pulsing glow animation for wins

## Data Models

### SlotsGame Model Schema

```python
class SlotsGame(models.Model):
    """Slots game instance."""
    
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
        choices=[(3, '3 барабана'), (5, '5 барабанов')],
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
        verbose_name='Server seed'
    )
    client_seed = models.CharField(
        max_length=64,
        verbose_name='Client seed'
    )
    nonce = models.IntegerField(
        default=0,
        verbose_name='Nonce'
    )
    server_seed_hash = models.CharField(
        max_length=64,
        verbose_name='Server seed hash'
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
            models.Index(fields=['user', '-created_at']),
        ]
```

### Win Combination Logic

The `check_win()` method implements different logic based on reel count:

**3-Reel Mode** (all 3 must match):
- 7️⃣ × 3 = 50x
- ⭐ × 3 = 25x
- 🔔 × 3 = 15x
- 🍊 × 3 = 10x
- 🍋 × 3 = 7x
- 🍒 × 3 = 5x

**5-Reel Mode**:

1. **Check 5-of-a-kind** (all 5 reels match):
   - 7️⃣ × 5 = 100x
   - ⭐ × 5 = 50x
   - 🔔 × 5 = 25x
   - 🍊 × 5 = 15x
   - 🍋 × 5 = 10x
   - 🍒 × 5 = 5x

2. **Check 3-consecutive** (first 3 reels match):
   - 7️⃣ × 3 = 20x
   - ⭐ × 3 = 10x
   - 🔔 × 3 = 5x

3. **No match**: multiplier = 0

**Algorithm**:
```python
def check_win(reels, reels_count):
    if reels_count == 3:
        # Check if all 3 match
        if all(symbol == reels[0] for symbol in reels):
            if reels[0] in MULTIPLIERS_3_REEL:
                return (MULTIPLIERS_3_REEL[reels[0]], f"3x {reels[0]}")
    
    elif reels_count == 5:
        # Check 5-of-a-kind
        if all(symbol == reels[0] for symbol in reels):
            if reels[0] in MULTIPLIERS_5X:
                return (MULTIPLIERS_5X[reels[0]], f"5x {reels[0]}")
        
        # Check 3-consecutive
        if reels[0] == reels[1] == reels[2]:
            if reels[0] in MULTIPLIERS_3X:
                return (MULTIPLIERS_3X[reels[0]], f"3x {reels[0]}")
    
    # No win
    return (Decimal('0.00'), "")
```

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Bet Validation
*For any* bet amount, the system should accept it if and only if it is a positive decimal value within the allowed range (MIN_BET to MAX_BET).
**Validates: Requirements 1.5**

### Property 2: Balance Verification Before Game Creation
*For any* user and bet amount, the system should verify the user's balance is sufficient before creating a game, rejecting the request if balance < bet_amount.
**Validates: Requirements 1.2**

### Property 3: Atomic Balance Deduction
*For any* valid game creation, the bet amount should be deducted from the player's balance immediately, and if the game creation fails, the balance should remain unchanged (transaction atomicity).
**Validates: Requirements 1.4, 11.3**

### Property 4: Reel Generation Produces Exactly 5 Valid Symbols
*For any* game, the generated reels should contain exactly 5 symbols, and each symbol should be from the valid set {🍒, 🍋, 🍊, ⭐, 🔔, 7️⃣}.
**Validates: Requirements 2.1, 2.2**

### Property 5: Provably Fair Determinism
*For any* combination of server_seed, client_seed, and nonce, calling the reel generation function multiple times should always produce identical reel results.
**Validates: Requirements 2.3, 10.2, 10.4**

### Property 6: Win Detection Correctness
*For any* reel configuration, the check_win function should return the highest applicable multiplier according to the win table, with 5-of-a-kind taking priority over 3-consecutive matches.
**Validates: Requirements 3.10, 3.11**

### Property 7: Payout Calculation
*For any* winning game, the win_amount should equal bet_amount multiplied by the multiplier.
**Validates: Requirements 4.1**

### Property 8: Balance Update on Win
*For any* winning game, the player's balance should increase by exactly the win_amount after the game completes.
**Validates: Requirements 4.2**

### Property 9: No Balance Increase on Loss
*For any* losing game (multiplier = 0), the player's balance should only decrease by the bet_amount with no additional winnings added.
**Validates: Requirements 4.3**

### Property 10: Complete Game Record Persistence
*For any* created game, the database record should contain all required fields: user reference, bet_amount, reels (5 symbols), multiplier, win_amount, winning_combination, server_seed, client_seed, nonce, server_seed_hash, and created_at timestamp.
**Validates: Requirements 1.1, 2.4, 4.4, 4.5, 9.1, 9.5, 10.1, 10.3**

### Property 11: User Game Isolation
*For any* user requesting their game history, the returned games should only include games where that user is the owner, excluding all other users' games.
**Validates: Requirements 6.1, 6.3**

### Property 12: Game History Ordering
*For any* game history request, the returned games should be ordered by creation timestamp in descending order (newest first).
**Validates: Requirements 7.4**

### Property 13: API Response Completeness
*For any* successful game creation API call, the response should include all required fields: game_id, bet_amount, reels, multiplier, win_amount, winning_combination, balance, server_seed_hash, client_seed, nonce, and created_at.
**Validates: Requirements 6.2, 7.2**

### Property 14: Default Client Seed
*For any* game created without an explicit client_seed parameter, the system should generate and use a default client_seed value.
**Validates: Requirements 10.5**

## Error Handling

### Error Categories

1. **Validation Errors** (HTTP 400):
   - Invalid bet amount (negative, zero, non-numeric, out of range)
   - Invalid request format (missing required fields, malformed JSON)

2. **Authorization Errors** (HTTP 401/403):
   - Unauthenticated requests
   - Accessing games belonging to other users

3. **Business Logic Errors** (HTTP 400):
   - Insufficient balance
   - Invalid game state

4. **Server Errors** (HTTP 500):
   - Database connection failures
   - Unexpected exceptions

### Error Response Format

All errors return JSON with consistent structure:
```json
{
    "success": false,
    "error": "Descriptive error message in Russian"
}
```

### Transaction Safety

All game creation operations use `@transaction.atomic` decorator to ensure:
- Balance deduction and game creation happen atomically
- If any step fails, all changes are rolled back
- No partial state (e.g., bet deducted but game not created)

### Retry Logic

For transient failures (database locks, network issues):
- Wallet service operations include retry logic
- Maximum 3 retry attempts with exponential backoff
- After retries exhausted, return error to user

## Testing Strategy

### Dual Testing Approach

The Slots game requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific win combination examples (5x 7️⃣, 3x ⭐, etc.)
- Edge cases (empty balance, maximum bet, boundary values)
- Error conditions (invalid inputs, authentication failures)
- Integration points (Wallet Service, Provably Fair Service)

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Invariants (balance changes, data persistence, determinism)
- Round-trip properties (Provably Fair verification)

### Property-Based Testing Configuration

**Library**: Use `hypothesis` for Python property-based testing

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Tag format: `# Feature: slots-game, Property N: [property description]`

**Example Test Structure**:
```python
from hypothesis import given, strategies as st
from decimal import Decimal

@given(
    bet_amount=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000.00')),
    user=st.from_model(User)
)
def test_property_4_reel_generation(bet_amount, user):
    """
    Feature: slots-game, Property 4: Reel Generation Produces Exactly 5 Valid Symbols
    
    For any game, the generated reels should contain exactly 5 symbols,
    and each symbol should be from the valid set.
    """
    game = SlotsGameService.create_and_play_game(user, bet_amount)
    
    assert len(game.reels) == 5
    valid_symbols = {'🍒', '🍋', '🍊', '⭐', '🔔', '7️⃣'}
    assert all(symbol in valid_symbols for symbol in game.reels)
```

### Test Coverage Requirements

**Service Layer Tests** (`test_slots_service.py`):
- All win combination detection (9 specific examples)
- Payout calculation for all multipliers
- Reel generation with Provably Fair
- Balance validation and deduction
- Error handling (insufficient balance, invalid bets)
- Property tests for all 14 properties

**API Tests** (`test_slots_api.py`):
- Successful game creation
- Game history retrieval
- Specific game retrieval
- Game verification
- Authentication requirements
- Error responses (400, 401, 404, 500)
- Response format validation

**Integration Tests**:
- Wallet Service integration (balance updates)
- Provably Fair Service integration (seed generation, determinism)
- Database transaction atomicity

### Win Combination Test Cases

Unit tests must cover all specific win combinations:

1. 5x 7️⃣ → 100x multiplier
2. 5x ⭐ → 50x multiplier
3. 5x 🔔 → 25x multiplier
4. 5x 🍊 → 15x multiplier
5. 5x 🍋 → 10x multiplier
6. 5x 🍒 → 5x multiplier
7. 3x 7️⃣ (consecutive) → 20x multiplier
8. 3x ⭐ (consecutive) → 10x multiplier
9. 3x 🔔 (consecutive) → 5x multiplier
10. No match → 0x multiplier
11. Priority test: [7️⃣, 7️⃣, 7️⃣, 7️⃣, 7️⃣] should return 100x (not 20x)

### Provably Fair Verification Tests

Tests must verify:
- Same seeds always produce same reels (determinism)
- Different seeds produce different reels (randomness)
- Server seed hash matches actual server seed
- Verification function correctly validates game results
- Client can independently verify any game outcome
