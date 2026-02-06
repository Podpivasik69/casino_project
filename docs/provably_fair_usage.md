# Provably Fair Service - Usage Guide

## Overview

The Provably Fair Service provides cryptographically secure game outcome generation that can be verified by players. This ensures that the casino cannot manipulate game results.

## How It Works

### 1. Before Game Starts

**Server:**
- Generates `server_seed` (kept secret)
- Creates hash of `server_seed` (shown to player)

**Client:**
- Provides `client_seed` (or auto-generated)
- Can see `server_seed_hash` but not `server_seed`

**Result:**
- Game outcome is now locked in (determined by seeds)
- Server cannot change outcome without changing `server_seed`
- If server changes `server_seed`, hash won't match

### 2. During Game

- Game uses seeds to generate mine positions
- Positions are deterministic (same seeds = same positions)
- Player plays without knowing mine positions

### 3. After Game

**Server:**
- Reveals `server_seed`

**Client:**
- Verifies `server_seed` matches `server_seed_hash`
- Regenerates mine positions using revealed seeds
- Confirms positions match actual game

## API Reference

### Generate Server Seed

```python
from games.services.provably_fair import ProvablyFairService

# Generate cryptographically secure server seed
server_seed = ProvablyFairService.generate_server_seed()
# Returns: "c3b3d6c8a5b3ba4942bdfba95cbe9affcdd953463763e6c8c927ad9fa6fdfd7f"

# Create hash for player verification
server_seed_hash = ProvablyFairService.hash_seed(server_seed)
# Returns: "8b180ec97c355effb14b52884ad2e299..."
```

### Generate Client Seed

```python
# Auto-generate client seed
client_seed = ProvablyFairService.generate_client_seed()
# Returns: "ad2a8510505162587e31b7b65c5f90fd"

# Or accept from player
client_seed = request.POST.get('client_seed', ProvablyFairService.generate_client_seed())
```

### Generate Mine Positions

```python
# Generate mine positions for Mines game
positions = ProvablyFairService.generate_mine_positions(
    server_seed="abc123",
    client_seed="def456",
    nonce=0,  # Game round number
    mine_count=5  # Number of mines (3-20)
)
# Returns: [(2, 0), (1, 4), (0, 2), (0, 1), (4, 2)]
```

### Verify Game Was Fair

```python
# After game ends, verify positions
is_valid = ProvablyFairService.verify_mine_positions(
    server_seed="abc123",
    client_seed="def456",
    nonce=0,
    mine_count=5,
    claimed_positions=[(2, 0), (1, 4), (0, 2), (0, 1), (4, 2)]
)
# Returns: True if positions match, False otherwise

# Verify server seed hash
is_valid = ProvablyFairService.verify_server_seed_hash(
    server_seed="abc123",
    server_seed_hash="5740798640faf328ba1234bdee24d0b3..."
)
# Returns: True if hash matches
```

## Complete Workflow Example

### Step 1: Create New Game

```python
from games.services.provably_fair import ProvablyFairService

# Server generates seeds
server_seed = ProvablyFairService.generate_server_seed()
server_seed_hash = ProvablyFairService.hash_seed(server_seed)
client_seed = ProvablyFairService.generate_client_seed()

# Show game info to player (before game starts)
game_info = ProvablyFairService.get_game_info(
    server_seed_hash=server_seed_hash,
    client_seed=client_seed,
    nonce=0,
    mine_count=5
)

# Save to database
game = MinesSession.objects.create(
    user=request.user,
    server_seed=server_seed,  # Keep secret!
    server_seed_hash=server_seed_hash,  # Show to player
    client_seed=client_seed,
    nonce=0,
    mine_count=5,
    status='active'
)

# Generate mine positions (server-side only)
mine_positions = ProvablyFairService.generate_mine_positions(
    server_seed=server_seed,
    client_seed=client_seed,
    nonce=0,
    mine_count=5
)

# Store positions in database
game.mine_positions = mine_positions
game.save()

# Return to player (WITHOUT server_seed or mine_positions)
return JsonResponse({
    'game_id': game.id,
    'server_seed_hash': server_seed_hash,
    'client_seed': client_seed,
    'nonce': 0,
    'mine_count': 5,
    'grid_size': 5
})
```

### Step 2: Player Clicks Cell

```python
def reveal_cell(request, game_id, row, col):
    game = MinesSession.objects.get(id=game_id, user=request.user)
    
    # Check if cell has mine
    is_mine = (row, col) in game.mine_positions
    
    if is_mine:
        # Game over - reveal server_seed
        game.status = 'lost'
        game.save()
        
        # Get verification info
        verification_info = ProvablyFairService.get_verification_info(
            server_seed=game.server_seed,  # Now revealed!
            client_seed=game.client_seed,
            nonce=game.nonce,
            mine_count=game.mine_count,
            mine_positions=game.mine_positions
        )
        
        return JsonResponse({
            'is_mine': True,
            'game_over': True,
            'verification': verification_info
        })
    else:
        # Safe cell
        return JsonResponse({
            'is_mine': False,
            'game_over': False
        })
```

### Step 3: Player Verifies Game

```python
# Client-side verification (JavaScript example)
async function verifyGame(verification) {
    // 1. Verify server seed hash
    const computedHash = await sha256(verification.server_seed);
    if (computedHash !== verification.server_seed_hash) {
        console.error('Server seed hash mismatch!');
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
    if (JSON.stringify(regeneratedPositions) !== JSON.stringify(verification.mine_positions)) {
        console.error('Mine positions mismatch!');
        return false;
    }
    
    console.log('Game verified as fair!');
    return true;
}
```

## Security Considerations

### ✅ DO:
- Generate `server_seed` using `ProvablyFairService.generate_server_seed()`
- Keep `server_seed` secret until game ends
- Show `server_seed_hash` to player before game starts
- Allow player to provide custom `client_seed`
- Increment `nonce` for each new game with same seeds
- Reveal `server_seed` after game ends

### ❌ DON'T:
- Reveal `server_seed` before game ends
- Change `server_seed` after showing hash to player
- Use predictable seeds (like timestamps)
- Reuse same `server_seed` + `client_seed` + `nonce` combination
- Skip verification step

## Algorithm Details

### HMAC-SHA256 Generation

```
message = client_seed + str(nonce)
hmac_hash = HMAC-SHA256(server_seed, message)
```

### Fisher-Yates Shuffle

```
1. Create array of all cell positions: [(0,0), (0,1), ..., (4,4)]
2. Use HMAC bytes to shuffle array
3. Select first mine_count positions
```

### Determinism

Same inputs always produce same output:
```python
# These will always produce identical positions
pos1 = generate_mine_positions("seed1", "seed2", 0, 5)
pos2 = generate_mine_positions("seed1", "seed2", 0, 5)
assert pos1 == pos2  # Always True
```

## Testing

Run the test suite:

```bash
python test_provably_fair.py
```

Tests cover:
- Seed generation (uniqueness, format)
- Hash generation (determinism, uniqueness)
- Mine position generation (validity, determinism)
- Position verification (valid/invalid cases)
- Complete workflow
- Distribution fairness

## Example Output

### Game Info (Before Game)
```json
{
  "server_seed_hash": "8b180ec97c355effb14b52884ad2e299...",
  "client_seed": "5ac7f71789baedd2c39c90ee3188a839",
  "nonce": 0,
  "mine_count": 5,
  "grid_size": 5,
  "total_cells": 25
}
```

### Verification Info (After Game)
```json
{
  "server_seed": "c3b3d6c8a5b3ba4942bdfba95cbe9aff...",
  "server_seed_hash": "8b180ec97c355effb14b52884ad2e299...",
  "client_seed": "5ac7f71789baedd2c39c90ee3188a839",
  "nonce": 0,
  "mine_count": 5,
  "mine_positions": [[2, 0], [1, 4], [0, 2], [0, 1], [4, 2]],
  "is_valid": true,
  "verification_url": "/verify?server_seed=c3b3d6c8...&client_seed=5ac7f717...&nonce=0"
}
```

## Resources

- [Provably Fair Gaming](https://en.wikipedia.org/wiki/Provably_fair)
- [HMAC-SHA256](https://en.wikipedia.org/wiki/HMAC)
- [Fisher-Yates Shuffle](https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle)
- [Cryptographic Hash Functions](https://en.wikipedia.org/wiki/Cryptographic_hash_function)
