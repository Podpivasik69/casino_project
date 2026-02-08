# Crash Game API Documentation

## Overview

The Crash Game is a real-time multiplayer betting game where players place bets and must cash out before a randomly generated crash point. The multiplier starts at 1.00x and grows continuously until it crashes.

## Game Flow

1. **WAITING**: Round is waiting to start (5-10 seconds countdown)
2. **ACTIVE**: Round is active, multiplier is growing from 1.00x
3. **CRASHED**: Round has crashed at predetermined crash point

## API Endpoints

### 1. Get Current Round

**Endpoint:** `GET /api/games/crash/current/`

**Authentication:** Required

**Description:** Get information about the current round and user's bets.

**Response (WAITING):**
```json
{
  "round_id": "3958baac-0b3c-424e-ad73-419ab2da03dd",
  "status": "waiting",
  "next_round_at": "2026-02-08T01:57:28.000Z",
  "seconds_until_start": 5
}
```

**Response (ACTIVE):**
```json
{
  "round_id": "3958baac-0b3c-424e-ad73-419ab2da03dd",
  "status": "active",
  "current_multiplier": "2.45",
  "started_at": "2026-02-08T01:57:20.000Z",
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
  "round_id": "3958baac-0b3c-424e-ad73-419ab2da03dd",
  "status": "crashed",
  "crash_point": "3.67",
  "crashed_at": "2026-02-08T01:57:25.000Z"
}
```

### 2. Place Bet

**Endpoint:** `POST /api/games/crash/bet/`

**Authentication:** Required

**Description:** Place a bet in the current round.

**Request Body:**
```json
{
  "amount": "10.00",
  "auto_cashout_target": "2.00"  // optional
}
```

**Parameters:**
- `amount` (required): Bet amount (min: 0.01, max: 1000.00)
- `auto_cashout_target` (optional): Auto cashout multiplier (min: 1.01)

**Response (Success):**
```json
{
  "bet_id": 123,
  "round_id": "3958baac-0b3c-424e-ad73-419ab2da03dd",
  "bet_amount": "10.00",
  "auto_cashout_target": "2.00",
  "status": "active",
  "balance": "990.00"
}
```

**Response (Error):**
```json
{
  "error": "Недостаточно средств"
}
```

**Error Codes:**
- `400`: Invalid bet amount, invalid round state, insufficient funds
- `401`: Not authenticated
- `500`: Server error

### 3. Cash Out

**Endpoint:** `POST /api/games/crash/cashout/`

**Authentication:** Required

**Description:** Cash out an active bet at the current multiplier.

**Request Body:**
```json
{
  "bet_id": 123
}
```

**Parameters:**
- `bet_id` (required): ID of the bet to cash out

**Response (Success):**
```json
{
  "bet_id": 123,
  "cashout_multiplier": "2.45",
  "win_amount": "24.50",
  "status": "cashed_out",
  "balance": "1014.50"
}
```

**Response (Error):**
```json
{
  "error": "Ставка уже не активна"
}
```

**Error Codes:**
- `400`: Invalid bet, bet not active, round not active
- `401`: Not authenticated
- `500`: Server error

### 4. Get Round History

**Endpoint:** `GET /api/games/crash/history/`

**Authentication:** Not required

**Description:** Get history of recent completed rounds.

**Response:**
```json
{
  "rounds": [
    {
      "round_id": "3958baac-0b3c-424e-ad73-419ab2da03dd",
      "crash_point": "3.67",
      "crashed_at": "2026-02-08T01:57:25.000Z"
    },
    {
      "round_id": "248e2899-991c-4c03-bde2-8d63d3e1a636",
      "crash_point": "5.31",
      "crashed_at": "2026-02-08T01:57:15.000Z"
    }
    // ... up to 50 rounds
  ]
}
```

## Game Rules

### Betting

- **Minimum bet:** 0.01 ₽
- **Maximum bet:** 1000.00 ₽
- **Maximum bets per round:** 5 bets per user
- Bets can only be placed during WAITING or early ACTIVE state

### Multiplier

- Starts at 1.00x
- Grows at rate of 0.01x per 100ms
- Crashes at predetermined crash point (1.00x to 10000.00x)
- Average crash point: ~1.03x (for 97% RTP)

### Cashout

- **Manual cashout:** Click "ЗАБРАТЬ" button at any time during ACTIVE round
- **Auto cashout:** Set target multiplier (min 1.01x) and system will automatically cash out when reached
- Win amount = bet amount × cashout multiplier

### Provably Fair

- Each round has unique server_seed and client_seed
- Crash point is calculated using HMAC-SHA256(server_seed, client_seed)
- Server seed hash is revealed before round starts
- Full server seed is revealed after round ends
- Players can verify crash point was predetermined

## Example Usage

### JavaScript Example

```javascript
// Poll for current round state
async function updateGameState() {
    const response = await fetch('/api/games/crash/current/', {
        method: 'GET',
        credentials: 'same-origin'
    });
    const data = await response.json();
    
    if (data.status === 'active') {
        console.log(`Current multiplier: ${data.current_multiplier}x`);
    }
}

// Place bet
async function placeBet(amount, autoCashout = null) {
    const response = await fetch('/api/games/crash/bet/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            amount: amount,
            auto_cashout_target: autoCashout
        })
    });
    
    const data = await response.json();
    if (response.ok) {
        console.log(`Bet placed: ${data.bet_id}`);
    } else {
        console.error(`Error: ${data.error}`);
    }
}

// Cash out
async function cashout(betId) {
    const response = await fetch('/api/games/crash/cashout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            bet_id: betId
        })
    });
    
    const data = await response.json();
    if (response.ok) {
        console.log(`Cashed out at ${data.cashout_multiplier}x for ${data.win_amount} ₽`);
    } else {
        console.error(`Error: ${data.error}`);
    }
}

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

### Python Example

```python
import requests

# Get current round
response = requests.get('http://localhost:8000/api/games/crash/current/')
data = response.json()
print(f"Status: {data['status']}")

# Place bet
response = requests.post(
    'http://localhost:8000/api/games/crash/bet/',
    json={
        'amount': '10.00',
        'auto_cashout_target': '2.00'
    },
    cookies={'sessionid': 'your_session_id'}
)
data = response.json()
print(f"Bet ID: {data['bet_id']}")

# Cash out
response = requests.post(
    'http://localhost:8000/api/games/crash/cashout/',
    json={'bet_id': 123},
    cookies={'sessionid': 'your_session_id'}
)
data = response.json()
print(f"Win: {data['win_amount']} ₽")
```

## Real-Time Updates

For best user experience, poll the `/api/games/crash/current/` endpoint every 100ms during active rounds to get real-time multiplier updates.

```javascript
let pollingInterval = null;

function startPolling() {
    pollingInterval = setInterval(updateGameState, 100);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
}
```

## Error Handling

Always handle errors gracefully:

```javascript
try {
    const response = await fetch('/api/games/crash/bet/', {
        method: 'POST',
        // ... request config
    });
    
    const data = await response.json();
    
    if (!response.ok) {
        // Handle API error
        alert(data.error || 'Произошла ошибка');
        return;
    }
    
    // Success
    console.log('Bet placed successfully');
    
} catch (error) {
    // Handle network error
    console.error('Network error:', error);
    alert('Ошибка соединения');
}
```

## Rate Limiting

- No rate limiting currently implemented
- Recommended: Poll at 100ms intervals (10 requests/second)
- Avoid excessive polling to reduce server load

## Support

For issues or questions, contact support or check the main documentation.
