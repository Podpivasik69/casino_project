# Tasks: Crash Game Implementation

## Phase 1: Models and Database

### Task 1.1: Create CrashRound Model
- [ ] 1.1 Add CrashRound model to games/models.py
  - Add RoundStatus choices (WAITING, ACTIVE, CRASHED)
  - Add fields: round_id (UUID), status, crash_point, server_seed, client_seed, server_seed_hash
  - Add timestamps: created_at, started_at, crashed_at, next_round_at
  - Add validators for crash_point (min 1.00)
  - Add indexes for status and created_at

### Task 1.2: Create CrashBet Model
- [ ] 1.2 Add CrashBet model to games/models.py
  - Add BetStatus choices (ACTIVE, CASHED_OUT, LOST)
  - Add relationships: user (FK), round (FK)
  - Add fields: bet_amount, cashout_multiplier, win_amount, status, auto_cashout_target
  - Add timestamps: created_at, cashed_out_at
  - Add validators for bet_amount (min 0.01) and auto_cashout_target (min 1.01)
  - Add indexes for user_id, round_id, status

### Task 1.3: Create and Run Migrations
- [ ] 1.3 Generate and apply database migrations
  - Run: python manage.py makemigrations games
  - Run: python manage.py migrate games
  - Verify tables created correctly

## Phase 2: Service Layer

### Task 2.1: Create CrashGameService Base
- [ ] 2.1 Create games/services/crash_service.py
  - Define CrashGameService class
  - Add constants: HOUSE_EDGE, MIN_BET, MAX_BET, MIN_CRASH_POINT, MAX_CRASH_POINT, WAITING_DURATION, MAX_BETS_PER_USER, MULTIPLIER_GROWTH_RATE
  - Import required dependencies (models, WalletService, ProvablyFairService)

### Task 2.2: Implement Crash Point Generation
- [ ] 2.2 Add calculate_crash_point() method
  - Use HMAC-SHA256 to combine server_seed and client_seed
  - Convert hash to random value [0, 1]
  - Apply formula: crash_point = (100 / 97) / random_value
  - Ensure crash_point >= MIN_CRASH_POINT
  - Cap at MAX_CRASH_POINT
  - Return Decimal value

### Task 2.3: Implement Round Management
- [ ] 2.3 Add round management methods
  - start_new_round(): Generate seeds, calculate crash_point, create CrashRound with WAITING status
  - activate_round(): Update status to ACTIVE, set started_at
  - get_current_round(): Return active or waiting round
  - crash_round(): Update status to CRASHED, set crashed_at, process lost bets

### Task 2.4: Implement Multiplier Calculation
- [ ] 2.4 Add get_current_multiplier() method
  - Calculate elapsed time since started_at in milliseconds
  - Apply formula: multiplier = 1.00 + (elapsed_ms / 100) * MULTIPLIER_GROWTH_RATE
  - Cap at crash_point
  - Return Decimal value with 2 decimal places

### Task 2.5: Implement Bet Placement
- [ ] 2.5 Add place_bet() method
  - Validate bet amount (MIN_BET <= amount <= MAX_BET)
  - Get current round (must be WAITING or early ACTIVE)
  - Check user doesn't exceed MAX_BETS_PER_USER
  - Deduct bet amount using WalletService.deduct()
  - Create CrashBet with status=ACTIVE
  - Handle auto_cashout_target if provided
  - Use @transaction.atomic decorator

### Task 2.6: Implement Manual Cashout
- [ ] 2.6 Add cashout() method
  - Get bet and verify ownership
  - Verify bet status is ACTIVE
  - Verify round is ACTIVE
  - Get current multiplier
  - Calculate win_amount = bet_amount * current_multiplier
  - Update bet: status=CASHED_OUT, cashout_multiplier, win_amount, cashed_out_at
  - Add winnings using WalletService.add()
  - Use @transaction.atomic decorator

### Task 2.7: Implement Auto Cashout Processing
- [ ] 2.7 Add process_auto_cashouts() method
  - Query ACTIVE bets with auto_cashout_target <= current_multiplier
  - For each bet: calculate win_amount using auto_cashout_target
  - Update bet status to CASHED_OUT
  - Add winnings using WalletService
  - Return count of processed bets

### Task 2.8: Implement History and User Bets
- [ ] 2.8 Add helper methods
  - get_round_history(): Return last 50 CRASHED rounds ordered by created_at DESC
  - get_user_bets(): Return user's bets for specific round

## Phase 3: API Endpoints

### Task 3.1: Create Crash Views File
- [ ] 3.1 Create games/views/crash_views.py
  - Import required dependencies
  - Import CrashGameService
  - Set up base view structure

### Task 3.2: Implement Current Round Endpoint
- [ ] 3.2 Add GET /api/games/crash/current/ endpoint
  - Get current round using CrashGameService.get_current_round()
  - If WAITING: return status, next_round_at, seconds_until_start
  - If ACTIVE: return status, current_multiplier, started_at, user_bets
  - If CRASHED: return status, crash_point, crashed_at, next_round_at
  - Require authentication

### Task 3.3: Implement Bet Placement Endpoint
- [ ] 3.3 Add POST /api/games/crash/bet/ endpoint
  - Parse request: amount, auto_cashout_target (optional)
  - Validate input data
  - Call CrashGameService.place_bet()
  - Return bet details and updated balance
  - Handle errors: insufficient funds, invalid amount, invalid round state
  - Require authentication

### Task 3.4: Implement Cashout Endpoint
- [ ] 3.4 Add POST /api/games/crash/cashout/ endpoint
  - Parse request: bet_id
  - Call CrashGameService.cashout()
  - Return cashout details and updated balance
  - Handle errors: invalid bet, bet not active, round crashed
  - Require authentication

### Task 3.5: Implement History Endpoint
- [ ] 3.5 Add GET /api/games/crash/history/ endpoint
  - Call CrashGameService.get_round_history()
  - Return list of rounds with round_id, crash_point, crashed_at
  - No authentication required (public data)

### Task 3.6: Update URL Configuration
- [ ] 3.6 Add crash endpoints to games/urls.py
  - Import crash_views
  - Add URL patterns for all crash endpoints
  - Use 'crash/' prefix

## Phase 4: Frontend Template

### Task 4.1: Create Base Template
- [ ] 4.1 Create templates/crash.html
  - Extend base.html
  - Add page title and meta tags
  - Create main container structure
  - Add CSS link for crash.css

### Task 4.2: Implement Graph Display
- [ ] 4.2 Add graph canvas and multiplier display
  - Add canvas element for graph animation
  - Add large multiplier display (e.g., "2.45x")
  - Add round status indicator
  - Add countdown timer for waiting state

### Task 4.3: Implement Betting Controls
- [ ] 4.3 Add betting interface
  - Add bet amount input field
  - Add "PLACE BET" button
  - Add auto-cashout target input (optional)
  - Add "CASHOUT" button (disabled by default)
  - Add balance display

### Task 4.4: Implement History Display
- [ ] 4.4 Add round history section
  - Add container for last 50 rounds
  - Display crash points with color coding (low=green, medium=yellow, high=red)
  - Add horizontal scrolling for history
  - Update history on each round completion

### Task 4.5: Implement Active Bets Display
- [ ] 4.5 Add user bets section
  - Display active bets with bet amount and potential win
  - Show auto-cashout target if configured
  - Update potential win in real-time
  - Show cashed out bets with final multiplier

## Phase 5: Frontend JavaScript

### Task 5.1: Create JavaScript File
- [ ] 5.1 Create static/js/games/crash.js
  - Set up module structure
  - Define global variables and constants
  - Add initialization function

### Task 5.2: Implement AJAX Polling
- [ ] 5.2 Add real-time updates
  - Poll /api/games/crash/current/ every 100ms
  - Update multiplier display
  - Update graph animation
  - Process auto-cashouts
  - Handle round state changes (WAITING -> ACTIVE -> CRASHED)

### Task 5.3: Implement Graph Animation
- [ ] 5.3 Add canvas drawing logic
  - Draw growing line from 1.00x to current multiplier
  - Use exponential curve for visual effect
  - Add grid lines and axis labels
  - Animate smoothly between updates

### Task 5.4: Implement Crash Animation
- [ ] 5.4 Add crash visual effects
  - Screen shake effect
  - Red flash overlay
  - Stop graph animation
  - Display final crash point
  - Play crash sound effect

### Task 5.5: Implement Betting Logic
- [ ] 5.5 Add bet placement functionality
  - Validate bet amount on client side
  - Send POST request to /api/games/crash/bet/
  - Update UI on success
  - Enable cashout button
  - Display error messages

### Task 5.6: Implement Cashout Logic
- [ ] 5.6 Add cashout functionality
  - Send POST request to /api/games/crash/cashout/
  - Update UI on success
  - Disable cashout button
  - Show win amount with animation
  - Update balance display

### Task 5.7: Implement History Updates
- [ ] 5.7 Add history refresh logic
  - Fetch history on page load
  - Update history when round crashes
  - Add new crash point to beginning of list
  - Remove oldest entry if > 50 rounds
  - Animate new entries

## Phase 6: Styling

### Task 6.1: Create CSS File
- [ ] 6.1 Create static/css/games/crash.css
  - Define color scheme (dark theme with neon accents)
  - Set up responsive layout
  - Add animation keyframes

### Task 6.2: Style Graph Area
- [ ] 6.2 Add graph styling
  - Style canvas container
  - Add border and shadow effects
  - Style multiplier display (large, bold, glowing)
  - Add status indicator styling

### Task 6.3: Style Controls
- [ ] 6.3 Add control styling
  - Style input fields
  - Style buttons (BET, CASHOUT)
  - Add hover and active states
  - Add disabled state styling
  - Add pulsing animation for active cashout button

### Task 6.4: Style History
- [ ] 6.4 Add history styling
  - Style crash point badges
  - Add color coding (green < 2x, yellow 2-5x, red > 5x)
  - Add horizontal scroll styling
  - Add hover effects

### Task 6.5: Add Animations
- [ ] 6.5 Implement CSS animations
  - Fade in/out transitions
  - Shake animation for crash
  - Pulse animation for buttons
  - Glow effects for multiplier
  - Slide animations for history updates

## Phase 7: Integration

### Task 7.1: Update Navigation
- [ ] 7.1 Add Crash to site navigation
  - Update templates/base.html navigation menu
  - Add "Crash" link with icon
  - Add active state styling

### Task 7.2: Update Home Page
- [ ] 7.2 Add Crash game card to home page
  - Update templates/home.html
  - Add Crash game card with description
  - Add thumbnail/icon
  - Add "Play Now" button

### Task 7.3: Update Main URLs
- [ ] 7.3 Add crash route to main urls
  - Update casino/urls.py
  - Add crash template view route
  - Test navigation

## Phase 8: Background Round Management

### Task 8.1: Create Round Manager
- [ ] 8.1 Implement automatic round progression
  - Create management command or Celery task
  - Start new round when no active round exists
  - Activate round after WAITING_DURATION
  - Crash round when multiplier reaches crash_point
  - Process auto-cashouts during active round
  - Loop continuously

### Task 8.2: Add Round Scheduler
- [ ] 8.2 Set up round scheduling
  - Configure Celery beat schedule (if using Celery)
  - Or create Django management command for manual control
  - Add error handling and logging
  - Test round progression

## Phase 9: Testing

### Task 9.1: Create Service Tests
- [ ] 9.1 Create test_crash_service.py
  - Test crash point generation (RTP ~97%)
  - Test round lifecycle (WAITING -> ACTIVE -> CRASHED)
  - Test bet placement (valid/invalid amounts)
  - Test manual cashout
  - Test auto-cashout processing
  - Test multiple bets per user
  - Test wallet integration

### Task 9.2: Create API Tests
- [ ] 9.2 Create test_crash_api.py
  - Test GET /current/ endpoint (all states)
  - Test POST /bet/ endpoint (success/error cases)
  - Test POST /cashout/ endpoint (success/error cases)
  - Test GET /history/ endpoint
  - Test authentication requirements

### Task 9.3: Create Integration Tests
- [ ] 9.3 Create test_crash_integration.py
  - Test complete game flow (bet -> cashout -> win)
  - Test complete game flow (bet -> crash -> loss)
  - Test auto-cashout flow
  - Test multiple users in same round
  - Test provably fair verification

### Task 9.4: Manual Testing
- [ ] 9.4 Perform manual testing
  - Test UI responsiveness
  - Test animations and effects
  - Test real-time updates
  - Test error handling
  - Test on different browsers
  - Test on mobile devices

## Phase 10: Documentation

### Task 10.1: Create API Documentation
- [ ] 10.1 Create docs/crash_api_usage.md
  - Document all endpoints
  - Add request/response examples
  - Document error codes
  - Add usage examples

### Task 10.2: Create User Guide
- [ ] 10.2 Create docs/crash_game_guide.md
  - Explain game rules
  - Explain betting strategies
  - Explain auto-cashout feature
  - Explain provably fair verification

### Task 10.3: Update Project Documentation
- [ ] 10.3 Update main documentation files
  - Update README.md with Crash game info
  - Update CHANGELOG.md
  - Update PROJECT_SUMMARY.md

## Phase 11: Polish and Optimization

### Task 11.1: Add Sound Effects
- [ ] 11.1* Implement audio
  - Add tick sound during multiplier growth
  - Add cashout success sound
  - Add crash sound effect
  - Add mute/unmute toggle

### Task 11.2: Add Advanced Features
- [ ] 11.2* Implement optional features
  - Add statistics panel (max win, average crash point)
  - Add leaderboard (highest cashout)
  - Add chat for players
  - Add bet presets (quick bet buttons)

### Task 11.3: Performance Optimization
- [ ] 11.3 Optimize performance
  - Add database indexes
  - Optimize queries (select_related, prefetch_related)
  - Add caching for round history
  - Optimize JavaScript polling
  - Test with multiple concurrent users

### Task 11.4: Security Review
- [ ] 11.4 Review security
  - Verify authentication on all endpoints
  - Check for race conditions in cashout
  - Verify wallet transaction atomicity
  - Test for edge cases and exploits
  - Add rate limiting

## Notes

- Tasks marked with * are optional enhancements
- Each task should be completed and tested before moving to the next
- Use @transaction.atomic for all database operations involving money
- Follow existing code patterns from Mines, Plinko, Dice, and Slots games
- Prioritize correctness over performance initially
- Test thoroughly with real money scenarios
