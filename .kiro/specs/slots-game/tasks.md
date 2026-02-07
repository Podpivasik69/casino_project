# Implementation Plan: Slots Game

## Overview

This implementation plan breaks down the Slots game feature into discrete coding tasks. The game follows the established patterns from Dice, Mines, and Plinko games, integrating with existing Wallet and Provably Fair services. Each task builds incrementally, with testing integrated throughout to catch errors early.

## Tasks

- [ ] 1. Create SlotsGame model and database migration
  - Add SlotsGame model to `games/models.py` with all required fields
  - Fields: user (ForeignKey), bet_amount, reels_count (IntegerField with choices 3 or 5), reels (JSONField), multiplier, win_amount, winning_combination, server_seed, client_seed, nonce, server_seed_hash, created_at
  - Add Meta class with verbose names, ordering, and indexes
  - Add model methods: `__str__()`, `is_win()`, `get_win_amount()`
  - Create and run database migration
  - _Requirements: 1.1, 1.6, 1.7, 9.1, 9.3, 9.6_

- [ ] 2. Implement SlotsGameService core logic
  - [ ] 2.1 Create service file and define constants
    - Create `games/services/slots_service.py`
    - Define MIN_BET, MAX_BET constants
    - Define SYMBOLS list: ['🍒', '🍋', '🍊', '⭐', '🔔', '7️⃣']
    - Define MULTIPLIERS_3_REEL dictionary (50x, 25x, 15x, 10x, 7x, 5x)
    - Define MULTIPLIERS_5X dictionary (100x, 50x, 25x, 15x, 10x, 5x)
    - Define MULTIPLIERS_3X dictionary (20x, 10x, 5x)
    - _Requirements: 2.3, 3.1-3.18_
  
  - [ ]* 2.2 Write property test for bet validation
    - **Property 1: Bet Validation**
    - **Validates: Requirements 1.5**
  
  - [ ] 2.3 Implement validate_bet() method
    - Validate bet_amount is within MIN_BET to MAX_BET range
    - Raise ValueError with descriptive Russian message if invalid
    - _Requirements: 1.5_
  
  - [ ]* 2.4 Write property test for reel generation
    - **Property 4: Reel Generation Produces Exactly 5 Valid Symbols**
    - **Validates: Requirements 2.1, 2.2**
  
  - [ ] 2.5 Implement generate_reels() method
    - Accept server_seed, client_seed, nonce, reels_count parameters
    - Call ProvablyFairService to generate 3 or 5 random symbols based on reels_count
    - Return list of 3 or 5 symbols from SYMBOLS set
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7_
  
  - [ ]* 2.6 Write property test for Provably Fair determinism
    - **Property 5: Provably Fair Determinism**
    - **Validates: Requirements 2.3, 10.2, 10.4**
  
  - [ ]* 2.7 Write unit tests for win detection (all combinations)
    - Test 3-reel mode: 3x 7️⃣ → 50x, 3x ⭐ → 25x, 3x 🔔 → 15x, 3x 🍊 → 10x, 3x 🍋 → 7x, 3x 🍒 → 5x
    - Test 5-reel mode: 5x 7️⃣ → 100x, 5x ⭐ → 50x, 5x 🔔 → 25x, 5x 🍊 → 15x, 5x 🍋 → 10x, 5x 🍒 → 5x
    - Test 5-reel mode: 3x 7️⃣ → 20x, 3x ⭐ → 10x, 3x 🔔 → 5x
    - Test no match → 0x for both modes
    - Test priority: 5x 7️⃣ returns 100x (not 20x)
    - _Requirements: 3.1-3.18_
  
  - [ ] 2.8 Implement check_win() method
    - Accept reels and reels_count parameters
    - For 3-reel mode: check if all 3 match
    - For 5-reel mode: check for 5-of-a-kind matches first (highest priority), then 3-consecutive matches
    - Return tuple of (multiplier, winning_combination_description)
    - Return (0, "") for no match
    - _Requirements: 3.1-3.18_
  
  - [ ]* 2.9 Write property test for win detection correctness
    - **Property 6: Win Detection Correctness**
    - **Validates: Requirements 3.10, 3.11**
  
  - [ ]* 2.10 Write property test for payout calculation
    - **Property 7: Payout Calculation**
    - **Validates: Requirements 4.1**
  
  - [ ] 2.11 Implement calculate_payout() method
    - Multiply bet_amount by multiplier
    - Return Decimal result
    - _Requirements: 4.1_

- [ ] 3. Implement game creation and transaction logic
  - [ ] 3.1 Implement create_and_play_game() method
    - Use @transaction.atomic decorator
    - Validate bet amount and reels_count (must be 3 or 5)
    - Default reels_count to 5 if not provided
    - Call WalletService.place_bet() to deduct bet
    - Generate Provably Fair seeds (server_seed, client_seed, nonce)
    - Generate server_seed_hash
    - Call generate_reels() with reels_count to get symbols
    - Call check_win() with reels and reels_count to determine multiplier and combination
    - Calculate win_amount using calculate_payout()
    - Create SlotsGame record with all fields including reels_count
    - If won, call WalletService.add_winnings()
    - Return SlotsGame instance
    - _Requirements: 1.1, 1.2, 1.4, 1.6-1.9, 2.1-2.7, 3.1-3.18, 4.1-4.5, 10.1-10.5_
  
  - [ ]* 3.2 Write property test for balance verification
    - **Property 2: Balance Verification Before Game Creation**
    - **Validates: Requirements 1.2**
  
  - [ ]* 3.3 Write property test for atomic balance deduction
    - **Property 3: Atomic Balance Deduction**
    - **Validates: Requirements 1.4, 11.3**
  
  - [ ]* 3.4 Write property test for balance update on win
    - **Property 8: Balance Update on Win**
    - **Validates: Requirements 4.2**
  
  - [ ]* 3.5 Write property test for no balance increase on loss
    - **Property 9: No Balance Increase on Loss**
    - **Validates: Requirements 4.3**
  
  - [ ]* 3.6 Write property test for complete game record persistence
    - **Property 10: Complete Game Record Persistence**
    - **Validates: Requirements 1.1, 2.4, 4.4, 4.5, 9.1, 9.5, 10.1, 10.3**
  
  - [ ]* 3.7 Write property test for default client seed
    - **Property 14: Default Client Seed**
    - **Validates: Requirements 10.5**

- [ ] 4. Checkpoint - Ensure core service tests pass
  - Run all service layer tests
  - Verify all property tests pass with 100+ iterations
  - Ensure all win combinations work correctly
  - Ask the user if questions arise

- [ ] 5. Implement game retrieval and history methods
  - [ ] 5.1 Implement get_user_games() method
    - Filter games by user
    - Order by created_at descending
    - Apply limit parameter (default 10)
    - Return QuerySet
    - _Requirements: 6.1, 7.4_
  
  - [ ] 5.2 Implement get_game_by_id() method
    - Accept game_id and optional user parameter
    - Filter by user if provided
    - Return SlotsGame instance or None
    - Handle DoesNotExist exception
    - _Requirements: 6.3_
  
  - [ ] 5.3 Implement verify_game() method
    - Accept SlotsGame instance
    - Regenerate reels using stored seeds and nonce
    - Compare with stored reels
    - Return True if match, False otherwise
    - _Requirements: 10.4_
  
  - [ ]* 5.4 Write property test for user game isolation
    - **Property 11: User Game Isolation**
    - **Validates: Requirements 6.1, 6.3**
  
  - [ ]* 5.5 Write property test for game history ordering
    - **Property 12: Game History Ordering**
    - **Validates: Requirements 7.4**

- [ ] 6. Implement API endpoints
  - [ ] 6.1 Create slots_views.py and implement create_game endpoint
    - Create `games/views/slots_views.py`
    - Implement POST /api/games/slots/create/
    - Parse JSON body (bet_amount, reels_count, optional client_seed)
    - Default reels_count to 5 if not provided
    - Validate reels_count is 3 or 5
    - Call SlotsGameService.create_and_play_game()
    - Calculate winnings
    - Get updated balance
    - Return JSON response with all game data including reels_count
    - Handle errors (ValueError, InsufficientFundsError, Exception)
    - Return appropriate HTTP status codes
    - _Requirements: 1.6-1.9, 7.1, 7.2, 7.3_
  
  - [ ] 6.2 Implement get_history endpoint
    - Implement GET /api/games/slots/history/
    - Parse limit query parameter (default 10, max 100)
    - Call SlotsGameService.get_user_games()
    - Format games as JSON array
    - Return JSON response
    - _Requirements: 6.1, 6.2, 7.4_
  
  - [ ] 6.3 Implement get_game endpoint
    - Implement GET /api/games/slots/<game_id>/
    - Call SlotsGameService.get_game_by_id()
    - Return 404 if game not found
    - Include all game details including Provably Fair fields
    - Return JSON response
    - _Requirements: 6.3, 10.3_
  
  - [ ] 6.4 Implement verify_game endpoint
    - Implement POST /api/games/slots/verify/
    - Parse game_id from JSON body
    - Call SlotsGameService.verify_game()
    - Return verification result
    - _Requirements: 10.4_
  
  - [ ]* 6.5 Write property test for API response completeness
    - **Property 13: API Response Completeness**
    - **Validates: Requirements 6.2, 7.2**
  
  - [ ]* 6.6 Write API integration tests
    - Test successful game creation
    - Test game history retrieval
    - Test specific game retrieval
    - Test game verification
    - Test authentication requirements
    - Test error responses (400, 401, 404, 500)
    - _Requirements: 7.1-7.5, 11.1-11.5_

- [ ] 7. Add URL routing
  - Update `games/urls.py` to include slots endpoints
  - Add path for create_game: 'slots/create/'
  - Add path for get_history: 'slots/history/'
  - Add path for get_game: 'slots/<int:game_id>/'
  - Add path for verify_game: 'slots/verify/'
  - _Requirements: 7.1_

- [ ] 8. Checkpoint - Ensure all API tests pass
  - Run all API tests
  - Test authentication and authorization
  - Verify error handling
  - Ask the user if questions arise

- [ ] 9. Create frontend template
  - [ ] 9.1 Create slots.html template
    - Create `templates/slots.html` extending base.html
    - Add mode selection buttons (3-reel / 5-reel) with active state styling
    - Add dynamic reel display containers (3 or 5 based on selected mode)
    - Add vertical scrolling animation containers for each reel with overflow hidden
    - Add bet amount selection buttons (1, 5, 10, 50, 100, custom input)
    - Add spin button with loading/spinning state
    - Add auto-spin toggle button
    - Add balance display with animated number updates
    - Add win/loss result display area with explosion effect container
    - Add winning combination display with glow effect
    - Add game history section
    - Include CSRF token for API calls
    - _Requirements: 8.1-8.5, 8.17-8.20_

- [ ] 10. Implement frontend JavaScript
  - [ ] 10.1 Create slots.js with core functionality
    - Create `static/js/games/slots.js`
    - Implement initSlotsGame() - initialize game state
    - Implement selectMode(reelsCount) - handle mode selection (3 or 5 reels)
    - Implement handleSpin() - handle spin button click
    - Implement createGame(betAmount, reelsCount) - call API to create game
    - Implement displayReels(reels) - display reel results
    - Implement displayResult(data) - show win/loss message
    - Implement updateBalance(balance) - update balance display with animation
    - Implement loadHistory() - fetch and display game history
    - Add error handling for API calls
    - _Requirements: 8.1-8.5, 8.17-8.20_
  
  - [ ] 10.2 Implement vertical scrolling reel animations
    - Implement animateReels(reelsCount) - start vertical scrolling for all reels
    - Create continuous symbol scrolling effect (symbols move top to bottom)
    - Implement stopReels(reels, reelsCount) - stop reels sequentially with stagger
    - Add random spin speeds for each reel (visual variety)
    - Implement smooth deceleration when stopping
    - Add CSS keyframes for vertical scroll animation
    - _Requirements: 8.6-8.11_
  
  - [ ] 10.3 Implement bounce and visual effects
    - Implement applyBounceEffect(reelElement) - overshoot and bounce back animation
    - Implement displayWinningCombination(reels, winningCombination) - highlight winning symbols
    - Add glowing border effect with pulsing animation for wins
    - Implement triggerJackpotAnimation() - explosion/burst effect for highest multipliers
    - Implement animateWinAmount(amount) - count up animation for win display
    - Add particle effects for jackpot (optional but recommended)
    - _Requirements: 8.9, 8.12-8.16_
  
  - [ ] 10.4 Implement auto-spin functionality
    - Implement handleAutoSpin() - toggle auto-spin mode
    - Implement autoSpinLoop() - continuous spinning
    - Stop on user action or insufficient balance
    - Disable manual spin during auto-spin
    - Show auto-spin status indicator
    - _Requirements: 8.17_

- [ ] 11. Create frontend CSS styling with advanced animations
  - Create `static/css/games/slots.css`
  - Style mode selection buttons (3-reel / 5-reel) with active states
  - Style reel containers with overflow:hidden for scrolling effect
  - Style symbols (large emoji display, centered, proper spacing)
  - Add vertical scroll animation keyframes (@keyframes scrollDown)
  - Add bounce animation keyframes (@keyframes bounceStop)
  - Add glow effect for winning symbols (box-shadow with animation)
  - Add pulsing glow animation keyframes (@keyframes pulseGlow)
  - Add explosion/burst effect for jackpots (scale, opacity, particles)
  - Style buttons (bet selection, spin, auto-spin) with hover/active/disabled states
  - Add smooth transitions for all state changes (transition: all 0.3s ease)
  - Implement responsive layout for both 3 and 5 reel modes
  - Style result display (win/loss messages, colors, animations)
  - Add number count-up animation for win amounts
  - _Requirements: 8.1-8.20_

- [ ] 12. Update home page with Slots game card
  - Update `templates/home.html`
  - Add Slots game card with icon, title, description
  - Add link to /slots/ page
  - Match styling of existing game cards (Mines, Plinko, Dice)
  - _Requirements: Integration requirement_

- [ ] 13. Add Slots page URL to main routing
  - Update main `urls.py` or appropriate URL configuration
  - Add path for slots page: 'slots/'
  - Map to view that renders slots.html template
  - _Requirements: Integration requirement_

- [ ] 14. Final integration and testing
  - [ ] 14.1 Manual testing checklist
    - Test mode selection (3-reel and 5-reel)
    - Test game creation with various bet amounts in both modes
    - Test all win combinations display correctly for both modes
    - Test vertical scrolling animation smoothness
    - Test bounce effect on reel stop
    - Test glow effect on winning combinations
    - Test jackpot explosion animation
    - Test balance updates correctly with animation
    - Test auto-spin starts and stops correctly
    - Test sequential reel stopping with stagger
    - Test game history displays correctly
    - Test Provably Fair verification works
    - Test responsive design on mobile
    - Test error messages display correctly
    - _Requirements: All requirements_
  
  - [ ] 14.2 Run full test suite
    - Run all unit tests
    - Run all property tests (verify 100+ iterations)
    - Run all API tests
    - Verify test coverage meets requirements
    - _Requirements: 12.1-12.6_

- [ ] 15. Final checkpoint - Complete feature verification
  - Ensure all tests pass
  - Verify integration with existing games
  - Verify Provably Fair system works correctly
  - Verify wallet transactions are atomic
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases for both 3-reel and 5-reel modes
- Integration tests verify service interactions
- Frontend tasks focus heavily on animations and visual effects
- Vertical scrolling animation is the core visual feature
- Bounce effect adds polish to reel stopping
- Glow and explosion effects enhance win feedback
- All monetary operations use Decimal type for precision
- All game operations are atomic (transaction.atomic)
- Follow existing patterns from Dice, Mines, and Plinko games
- 3-reel mode is for quick gameplay with simpler payouts
- 5-reel mode offers more winning combinations and higher multipliers
