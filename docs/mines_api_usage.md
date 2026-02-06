# Mines Game API - Usage Guide

## Overview

Mines is a provably fair game where players reveal cells on a 5x5 grid while avoiding mines. The more cells revealed without hitting a mine, the higher the multiplier and potential winnings.

## Game Rules

- **Grid Size**: 5x5 (25 cells total)
- **Mine Count**: 3-20 mines per game
- **Bet Amount**: Minimum 0.01, maximum depends on balance
- **Multiplier**: Increases with each safe cell revealed
- **Provably Fair**: All mine positions are cryptographically verifiable

## API Endpoints

### 1. Create Game

Create a new Mines game and place bet.

**Endpoint**: `POST /api/games/mines/create/`

**Request Body**:
```json
{
  "bet_amount": "10.00",
  "mine_count": 5,
  "client_seed": "optional_custom_seed"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "game_id": 123,
  "bet_amount": "10.00",
  "mine_count": 5,
  "server_seed_hash": "0d9c93d726775fc1e8a6c78c02395844...",
  "client_seed": "b372c55001b82f8fda532ea0b42c3600",
  "nonce": 0,
  "current_multiplier": "1.00",
  "grid_size": 5,
  "state": "active"
}
```

**Errors**:
- `400`: Invalid parameters or insufficient funds
- `401`: Not authenticated

**Example (curl)**:
```bash
curl -X POST http://localhost:8000/api/games/mines/create/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "bet_amount": "10.00",
    "mine_count": 5
  }'
```

---

### 2. Get Game Details

Retrieve current game state.

**Endpoint**: `GET /api/games/mines/<game_id>/`

**Response** (200 OK):
```json
{
  "game_id": 123,
  "bet_amount": "10.00",
  "mine_count": 5,
  "state": "active",
  "current_multiplier": "1.25",
  "opened_cells": [[0, 1]],
  "opened_count": 1,
  "server_seed_hash": "0d9c93d726775fc1...",
  "client_seed": "b372c55001b82f8f...",
  "nonce": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "ended_at": null
}
```

**Note**: `mine_positions` are only included if game has ended.

**Errors**:
- `404`: Game not found
- `401`: Not authenticated

**Example (curl)**:
```bash
curl http://localhost:8000/api/games/mines/123/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

### 3. Open Cell

Reveal a cell on the grid.

**Endpoint**: `POST /api/games/mines/<game_id>/open/`

**Request Body**:
```json
{
  "row": 2,
  "col": 3
}
```

**Response - Safe Cell** (200 OK):
```json
{
  "success": true,
  "is_mine": false,
  "multiplier": "1.25",
  "game_state": "active",
  "opened_cells": [[0, 1], [2, 3]],
  "opened_count": 2,
  "safe_cells_remaining": 18
}
```

**Response - Mine Hit** (200 OK):
```json
{
  "success": false,
  "is_mine": true,
  "multiplier": "0.00",
  "game_state": "lost",
  "opened_cells": [[0, 1]],
  "mine_positions": [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]],
  "verification": {
    "server_seed": "6ba54fc2224f368b...",
    "server_seed_hash": "0d9c93d726775fc1...",
    "client_seed": "b372c55001b82f8f...",
    "nonce": 0
  }
}
```

**Errors**:
- `400`: Invalid coordinates, cell already opened, or game ended
- `404`: Game not found
- `401`: Not authenticated

**Example (curl)**:
```bash
curl -X POST http://localhost:8000/api/games/mines/123/open/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "row": 2,
    "col": 3
  }'
```

---

### 4. Cashout

Cash out current winnings and end the game.

**Endpoint**: `POST /api/games/mines/<game_id>/cashout/`

**Response** (200 OK):
```json
{
  "success": true,
  "winnings": "12.50",
  "multiplier": "1.25",
  "game_state": "cashed_out",
  "mine_positions": [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]],
  "verification": {
    "server_seed": "6ba54fc2224f368b...",
    "server_seed_hash": "0d9c93d726775fc1...",
    "client_seed": "b372c55001b82f8f...",
    "nonce": 0
  }
}
```

**Errors**:
- `400`: Game not active or no cells opened
- `404`: Game not found
- `401`: Not authenticated

**Example (curl)**:
```bash
curl -X POST http://localhost:8000/api/games/mines/123/cashout/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

### 5. Verify Game

Get provably fair verification data (only available after game ends).

**Endpoint**: `GET /api/games/mines/<game_id>/verify/`

**Response** (200 OK):
```json
{
  "server_seed": "6ba54fc2224f368b63125fc105d939675336749096958dd89ee5b3209e74a558",
  "server_seed_hash": "0d9c93d726775fc1e8a6c78c02395844aff9ff7ac48419703843438564e44d46",
  "client_seed": "b372c55001b82f8fda532ea0b42c3600",
  "nonce": 0,
  "mine_count": 5,
  "mine_positions": [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]],
  "is_valid": true
}
```

**Errors**:
- `400`: Game still active
- `404`: Game not found
- `401`: Not authenticated

**Example (curl)**:
```bash
curl http://localhost:8000/api/games/mines/123/verify/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

## Complete Workflow Example

### Step 1: Create Game

```bash
curl -X POST http://localhost:8000/api/games/mines/create/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "bet_amount": "10.00",
    "mine_count": 5
  }'
```

Response:
```json
{
  "success": true,
  "game_id": 123,
  "server_seed_hash": "0d9c93d726775fc1...",
  "current_multiplier": "1.00"
}
```

### Step 2: Open Safe Cells

```bash
# Open cell (0, 0)
curl -X POST http://localhost:8000/api/games/mines/123/open/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{"row": 0, "col": 0}'

# Response: {"is_mine": false, "multiplier": "1.25"}

# Open cell (0, 1)
curl -X POST http://localhost:8000/api/games/mines/123/open/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{"row": 0, "col": 1}'

# Response: {"is_mine": false, "multiplier": "1.58"}

# Open cell (0, 2)
curl -X POST http://localhost:8000/api/games/mines/123/open/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{"row": 0, "col": 2}'

# Response: {"is_mine": false, "multiplier": "2.02"}
```

### Step 3: Cashout

```bash
curl -X POST http://localhost:8000/api/games/mines/123/cashout/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

Response:
```json
{
  "success": true,
  "winnings": "20.20",
  "multiplier": "2.02",
  "mine_positions": [[1, 0], [2, 1], [3, 2], [4, 3], [4, 4]]
}
```

### Step 4: Verify Game

```bash
curl http://localhost:8000/api/games/mines/123/verify/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

Response:
```json
{
  "server_seed": "6ba54fc2224f368b...",
  "is_valid": true
}
```

---

## Multiplier Calculation

The multiplier increases with each safe cell revealed according to the formula:

```
multiplier = product of (25 - i) / (25 - mine_count - i) for i in range(opened_cells)
```

**Examples**:

| Mines | Opened Cells | Multiplier |
|-------|--------------|------------|
| 5     | 0            | 1.00x      |
| 5     | 1            | 1.25x      |
| 5     | 2            | 1.58x      |
| 5     | 3            | 2.02x      |
| 10    | 1            | 1.67x      |
| 10    | 2            | 2.86x      |
| 20    | 1            | 5.00x      |
| 20    | 2            | 30.00x     |

**Maximum Multipliers**:
- 3 mines: 2.60x (opening 20 cells)
- 5 mines: 5.25x (opening 18 cells)
- 10 mines: 50.40x (opening 13 cells)
- 20 mines: 504.00x (opening 3 cells)

---

## Provably Fair Verification

### How It Works

1. **Before Game**: Server generates `server_seed` (kept secret) and shows you `server_seed_hash`
2. **During Game**: You provide `client_seed` (or use auto-generated)
3. **Mine Generation**: Positions are generated using `HMAC-SHA256(server_seed, client_seed + nonce)`
4. **After Game**: Server reveals `server_seed` for verification

### Verification Steps

1. **Verify Server Seed Hash**:
   ```javascript
   SHA256(server_seed) === server_seed_hash
   ```

2. **Regenerate Mine Positions**:
   ```javascript
   positions = HMAC_SHA256(server_seed, client_seed + nonce)
   ```

3. **Compare Positions**:
   ```javascript
   regenerated_positions === claimed_positions
   ```

### Example Verification (JavaScript)

```javascript
async function verifyGame(verification) {
  // 1. Verify server seed hash
  const computedHash = await sha256(verification.server_seed);
  if (computedHash !== verification.server_seed_hash) {
    return false;
  }
  
  // 2. Regenerate mine positions
  const regeneratedPositions = generateMinePositions(
    verification.server_seed,
    verification.client_seed,
    verification.nonce,
    verification.mine_count
  );
  
  // 3. Compare positions
  return JSON.stringify(regeneratedPositions) === 
         JSON.stringify(verification.mine_positions);
}
```

---

## Error Handling

### Common Errors

**400 Bad Request**:
```json
{
  "error": "Количество мин должно быть от 3 до 20"
}
```

**401 Unauthorized**:
```json
{
  "error": "Требуется авторизация"
}
```

**404 Not Found**:
```json
{
  "error": "Игра не найдена"
}
```

**500 Internal Server Error**:
```json
{
  "error": "Внутренняя ошибка сервера"
}
```

---

## Testing

### Run Service Tests

```bash
python test_mines_service.py
```

### Run API Tests

```bash
python test_mines_api.py
```

---

## Best Practices

1. **Always verify games** after they end to ensure fairness
2. **Use custom client seeds** for additional security
3. **Check balance** before creating games
4. **Handle errors gracefully** in your client application
5. **Store verification data** for later review
6. **Don't trust the client** - all validation happens server-side

---

## Rate Limiting

Currently no rate limiting is implemented. For production:
- Implement rate limiting per user
- Add CSRF protection for non-API requests
- Use proper authentication tokens instead of session cookies

---

## Support

For issues or questions:
- Check logs in `logs/casino.log`
- Review test files for usage examples
- See `docs/provably_fair_usage.md` for algorithm details
