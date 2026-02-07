# Slots Game Specification Summary

## 🎰 Overview

Dual-mode slot machine game with stunning vertical scrolling animations:
- **3-Reel Mode**: Classic quick gameplay (multipliers: 5x-50x)
- **5-Reel Mode**: Extended gameplay with more combinations (multipliers: 5x-100x)

## 🎨 Key Features

### Backend
1. **Dual Mode Support**
   - `reels_count` field (3 or 5)
   - Separate payout tables for each mode
   - Dynamic reel generation based on mode

2. **Payout Tables**
   - **3-Reel**: All 3 match (7️⃣=50x, ⭐=25x, 🔔=15x, 🍊=10x, 🍋=7x, 🍒=5x)
   - **5-Reel (5-of-a-kind)**: All 5 match (7️⃣=100x, ⭐=50x, 🔔=25x, 🍊=15x, 🍋=10x, 🍒=5x)
   - **5-Reel (3-consecutive)**: First 3 match (7️⃣=20x, ⭐=10x, 🔔=5x)

3. **Provably Fair Integration**
   - Server/client seeds
   - Verifiable randomness
   - Nonce tracking

### Frontend - СУПЕР АНИМАЦИИ! 🎬

1. **Vertical Scrolling Animation**
   - Symbols scroll from top to bottom continuously
   - Each reel has random spin speed
   - Smooth deceleration when stopping
   - Sequential stop with stagger effect (left to right)

2. **Bounce Effect**
   - Reels overshoot slightly when stopping
   - Bounce back to final position
   - Adds realistic physics feel

3. **Visual Effects**
   - **Glow Effect**: Winning symbols get pulsing glowing borders
   - **Jackpot Explosion**: Burst/particle animation for highest wins
   - **Number Count-Up**: Win amount animates from 0 to final value
   - **Balance Animation**: Smooth transitions on balance updates

4. **User Experience**
   - Mode selection buttons (3 / 5 reels)
   - Dynamic reel display based on mode
   - Clear visual feedback for all states
   - Responsive design for mobile

## 📁 File Structure

```
games/
├── models.py                    # SlotsGame model with reels_count
├── services/
│   └── slots_service.py        # Service with dual-mode logic
└── views/
    └── slots_views.py          # API endpoints

templates/
└── slots.html                  # Template with mode selection

static/
├── css/games/
│   └── slots.css              # Advanced animations CSS
└── js/games/
    └── slots.js               # Animation logic JS
```

## 🎯 API Endpoints

### POST /api/games/slots/create/
```json
{
  "bet_amount": "10.00",
  "reels_count": 5,           // 3 or 5
  "client_seed": "optional"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "game_id": 123,
    "reels_count": 5,
    "reels": ["🍒", "🍋", "🍊", "⭐", "🔔"],
    "multiplier": "10.00",
    "win_amount": "100.00",
    "winning_combination": "5x 🍋",
    "balance": "190.00"
  }
}
```

## 🎨 Animation Details

### CSS Keyframes
```css
@keyframes scrollDown {
  /* Vertical scrolling effect */
}

@keyframes bounceStop {
  /* Overshoot and bounce back */
}

@keyframes pulseGlow {
  /* Pulsing glow for wins */
}

@keyframes jackpotBurst {
  /* Explosion effect */
}
```

### JavaScript Functions
- `animateReels(reelsCount)` - Start vertical scroll
- `stopReels(reels, reelsCount)` - Sequential stop with stagger
- `applyBounceEffect(reelElement)` - Bounce animation
- `displayWinningCombination()` - Glow effect
- `triggerJackpotAnimation()` - Explosion effect
- `animateWinAmount(amount)` - Count-up animation

## 🚀 Implementation Priority

1. **Backend** (Tasks 1-8)
   - Model with reels_count
   - Service with dual-mode logic
   - API endpoints
   - Tests

2. **Frontend Structure** (Task 9)
   - Template with mode selection
   - Dynamic reel containers

3. **Core Animations** (Task 10.2)
   - Vertical scrolling
   - Sequential stopping
   - Smooth deceleration

4. **Visual Effects** (Task 10.3)
   - Bounce effect
   - Glow effect
   - Jackpot explosion

5. **Polish** (Task 11)
   - CSS refinement
   - Responsive design
   - Performance optimization

## 📊 Testing Focus

- All win combinations for both modes
- Animation smoothness
- Mode switching
- Provably Fair verification
- Balance updates
- Error handling

## 🎯 Success Criteria

✅ Smooth vertical scrolling animation
✅ Realistic bounce effect on stop
✅ Beautiful glow effect on wins
✅ Impressive jackpot explosion
✅ Both 3-reel and 5-reel modes work perfectly
✅ All animations are smooth (60fps)
✅ Responsive on mobile
✅ Provably Fair verification passes

---

**Next Steps**: Start with Task 1 (Model creation) and work through sequentially!
