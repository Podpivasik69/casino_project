# Requirements Document: Crash Game

## Introduction

The Crash Game is a real-time multiplayer betting game where players place bets and must cash out before a randomly generated crash point. A multiplier starts at 1.00x and grows continuously until it crashes. Players who cash out before the crash win their bet multiplied by the current multiplier; those who don't cash out in time lose their bet. The game features dramatic animations, real-time updates, provably fair mechanics, and a target RTP of approximately 97%.

## Glossary

- **Crash_Game**: The system managing crash game rounds
- **Crash_Round**: A single game instance with a unique crash point
- **Multiplier**: The current growth value starting from 1.00x
- **Crash_Point**: The predetermined multiplier value where the round ends
- **Player**: A user participating in the crash game
- **Bet**: A wager placed by a player in a crash round
- **Cashout**: The action of claiming winnings at the current multiplier
- **Auto_Cashout**: A preset multiplier at which the system automatically cashes out
- **RTP**: Return to Player percentage (target: 97%)
- **House_Edge**: The casino's advantage (3% for 97% RTP)
- **Provably_Fair**: Cryptographic verification system for crash point generation
- **Server_Seed**: Server-generated random value for crash point calculation
- **Client_Seed**: Player-provided value for crash point verification
- **Wallet_Service**: The system managing player balances and transactions
- **Round_Status**: The state of a crash round (waiting/active/crashed)
- **Bet_Status**: The state of a player's bet (active/cashed_out/lost)

## Requirements

### Requirement 1: Round Management

**User Story:** As a player, I want crash game rounds to start and end automatically, so that I can continuously play without manual intervention.

#### Acceptance Criteria

1. WHEN a crash round starts, THE Crash_Game SHALL initialize the multiplier at 1.00x and set the round status to active
2. WHEN a crash round is active, THE Crash_Game SHALL increment the multiplier continuously until it reaches the predetermined crash point
3. WHEN the multiplier reaches the crash point, THE Crash_Game SHALL set the round status to crashed and process all remaining active bets as losses
4. WHEN a crash round ends, THE Crash_Game SHALL start a new round after a waiting period of 5-10 seconds
5. THE Crash_Game SHALL generate a unique round identifier for each crash round

### Requirement 2: Crash Point Generation

**User Story:** As a casino operator, I want crash points to be generated with a controlled house edge, so that the game maintains a target RTP of 97%.

#### Acceptance Criteria

1. WHEN generating a crash point, THE Crash_Game SHALL use the formula: crash_point = (100 / (100 - house_edge)) / random_value where house_edge = 3
2. WHEN generating a crash point, THE Crash_Game SHALL ensure the random value is between 0 (exclusive) and 1 (inclusive)
3. WHEN generating a crash point, THE Crash_Game SHALL ensure the crash point is at least 1.00x
4. WHEN generating a crash point, THE Crash_Game SHALL store the crash point before the round becomes active
5. THE Crash_Game SHALL use server seed and client seed values for crash point generation to enable provably fair verification

### Requirement 3: Bet Placement

**User Story:** As a player, I want to place bets on active crash rounds, so that I can participate in the game.

#### Acceptance Criteria

1. WHEN a player places a bet, THE Crash_Game SHALL verify the player has sufficient balance in their wallet
2. WHEN a player places a bet in an active round, THE Crash_Game SHALL deduct the bet amount from the player's wallet immediately
3. WHEN a player places a bet, THE Crash_Game SHALL create a bet record with status set to active
4. WHEN a player attempts to place a bet in a crashed round, THE Crash_Game SHALL reject the bet and return an error
5. WHEN a player attempts to place a bet with an amount less than the minimum (0.01), THE Crash_Game SHALL reject the bet and return an error
6. WHEN a player places a bet, THE Crash_Game SHALL associate the bet with the current crash round

### Requirement 4: Manual Cashout

**User Story:** As a player, I want to cash out my bet at any time during an active round, so that I can secure my winnings at the current multiplier.

#### Acceptance Criteria

1. WHEN a player cashes out an active bet, THE Crash_Game SHALL calculate the win amount as bet_amount multiplied by the current multiplier
2. WHEN a player cashes out an active bet, THE Crash_Game SHALL add the win amount to the player's wallet
3. WHEN a player cashes out an active bet, THE Crash_Game SHALL update the bet status to cashed_out and record the cashout multiplier
4. WHEN a player attempts to cash out a bet that is not active, THE Crash_Game SHALL reject the cashout and return an error
5. WHEN a player attempts to cash out after the round has crashed, THE Crash_Game SHALL reject the cashout and return an error

### Requirement 5: Auto Cashout

**User Story:** As a player, I want to set an automatic cashout multiplier, so that my bet is cashed out automatically when the multiplier reaches my target.

#### Acceptance Criteria

1. WHEN a player configures auto cashout, THE Crash_Game SHALL store the target multiplier with the player's bet
2. WHEN the current multiplier reaches or exceeds a bet's auto cashout target, THE Crash_Game SHALL automatically cash out that bet
3. WHEN auto cashout is triggered, THE Crash_Game SHALL calculate winnings using the auto cashout target multiplier (not the current multiplier)
4. WHEN a player sets an auto cashout multiplier below 1.01x, THE Crash_Game SHALL reject the configuration and return an error
5. WHERE a player has configured auto cashout, WHEN the player manually cashes out before the target is reached, THE Crash_Game SHALL process the manual cashout and ignore the auto cashout setting

### Requirement 6: Bet Loss Processing

**User Story:** As a casino operator, I want bets that are not cashed out before the crash to be processed as losses, so that the game mechanics are enforced correctly.

#### Acceptance Criteria

1. WHEN a crash round ends, THE Crash_Game SHALL identify all bets with status active
2. WHEN processing lost bets, THE Crash_Game SHALL update each bet's status to lost
3. WHEN processing lost bets, THE Crash_Game SHALL set the win amount to zero
4. WHEN processing lost bets, THE Crash_Game SHALL not modify the player's wallet balance (bet amount was already deducted)
5. THE Crash_Game SHALL process all lost bets before starting a new round

### Requirement 7: Real-Time Multiplier Updates

**User Story:** As a player, I want to see the multiplier update in real-time, so that I can make informed decisions about when to cash out.

#### Acceptance Criteria

1. WHEN a crash round is active, THE Crash_Game SHALL provide the current multiplier value through an API endpoint
2. WHEN the multiplier is requested, THE Crash_Game SHALL calculate it based on the elapsed time since round start
3. WHEN the multiplier reaches the crash point, THE Crash_Game SHALL return the crash point value (not a higher value)
4. THE Crash_Game SHALL update the multiplier at least 10 times per second during active rounds
5. WHEN a round is in waiting status, THE Crash_Game SHALL return the time remaining until the next round starts

### Requirement 8: Round History

**User Story:** As a player, I want to view the history of recent crash rounds, so that I can analyze patterns and make betting decisions.

#### Acceptance Criteria

1. WHEN a player requests round history, THE Crash_Game SHALL return the most recent 50 completed rounds
2. WHEN returning round history, THE Crash_Game SHALL include the round identifier, crash point, and timestamp for each round
3. WHEN returning round history, THE Crash_Game SHALL order rounds from most recent to oldest
4. THE Crash_Game SHALL persist round history across server restarts
5. WHEN a round completes, THE Crash_Game SHALL add it to the round history immediately

### Requirement 9: Provably Fair Verification

**User Story:** As a player, I want to verify that crash points are determined fairly, so that I can trust the game is not rigged.

#### Acceptance Criteria

1. WHEN a crash round is created, THE Crash_Game SHALL generate a server seed and accept a client seed
2. WHEN generating a crash point, THE Crash_Game SHALL use both server seed and client seed in the calculation
3. WHEN a round completes, THE Crash_Game SHALL reveal the server seed to all players
4. WHEN a player requests verification, THE Crash_Game SHALL provide the server seed, client seed, and crash point for any completed round
5. THE Crash_Game SHALL use a cryptographic hash function to combine seeds for crash point generation

### Requirement 10: Wallet Integration

**User Story:** As a player, I want my bets and winnings to be reflected in my wallet balance, so that I can track my funds accurately.

#### Acceptance Criteria

1. WHEN a player places a bet, THE Crash_Game SHALL use the Wallet_Service to deduct the bet amount
2. WHEN a player cashes out, THE Crash_Game SHALL use the Wallet_Service to add the win amount
3. WHEN a wallet transaction fails, THE Crash_Game SHALL reject the bet or cashout and return an error
4. THE Crash_Game SHALL create transaction records for all bets and cashouts
5. WHEN a bet is placed, THE Crash_Game SHALL record the transaction type as "crash_bet"
6. WHEN a cashout occurs, THE Crash_Game SHALL record the transaction type as "crash_win"

### Requirement 11: Current Round Information

**User Story:** As a player, I want to view information about the current round, so that I can decide whether to place a bet.

#### Acceptance Criteria

1. WHEN a player requests current round information, THE Crash_Game SHALL return the round status (waiting/active/crashed)
2. WHEN the round is active, THE Crash_Game SHALL return the current multiplier
3. WHEN the round is waiting, THE Crash_Game SHALL return the time remaining until the next round starts
4. WHEN the round is crashed, THE Crash_Game SHALL return the crash point
5. THE Crash_Game SHALL return the round identifier for the current round

### Requirement 12: Player Bet Information

**User Story:** As a player, I want to view my active bets in the current round, so that I know when I can cash out.

#### Acceptance Criteria

1. WHEN a player requests their bet information, THE Crash_Game SHALL return all active bets for that player in the current round
2. WHEN returning bet information, THE Crash_Game SHALL include the bet amount, current potential win, and auto cashout target (if configured)
3. WHEN a player has no active bets, THE Crash_Game SHALL return an empty list
4. WHEN a player has cashed out, THE Crash_Game SHALL include the cashout multiplier and win amount in the bet information
5. THE Crash_Game SHALL update bet information in real-time as the multiplier changes

### Requirement 13: Multiple Bets Per Round

**User Story:** As a player, I want to place multiple bets in a single round with different auto cashout targets, so that I can implement diverse betting strategies.

#### Acceptance Criteria

1. WHEN a player places multiple bets in the same round, THE Crash_Game SHALL accept all bets if the player has sufficient balance
2. WHEN processing multiple bets, THE Crash_Game SHALL deduct the total bet amount from the player's wallet
3. WHEN a player cashes out, THE Crash_Game SHALL allow the player to specify which bet to cash out
4. WHERE a player has multiple bets with different auto cashout targets, THE Crash_Game SHALL cash out each bet independently when its target is reached
5. THE Crash_Game SHALL allow a maximum of 5 active bets per player per round

### Requirement 14: Minimum and Maximum Bet Limits

**User Story:** As a casino operator, I want to enforce minimum and maximum bet limits, so that the game remains balanced and fair.

#### Acceptance Criteria

1. THE Crash_Game SHALL enforce a minimum bet amount of 0.01
2. THE Crash_Game SHALL enforce a maximum bet amount of 1000.00
3. WHEN a player attempts to place a bet below the minimum, THE Crash_Game SHALL reject the bet and return an error
4. WHEN a player attempts to place a bet above the maximum, THE Crash_Game SHALL reject the bet and return an error
5. THE Crash_Game SHALL validate bet amounts before deducting from the player's wallet

### Requirement 15: Error Handling

**User Story:** As a player, I want to receive clear error messages when something goes wrong, so that I understand what happened and can take corrective action.

#### Acceptance Criteria

1. WHEN an error occurs, THE Crash_Game SHALL return a descriptive error message
2. WHEN a player has insufficient balance, THE Crash_Game SHALL return an error message indicating the required amount
3. WHEN a player attempts an invalid action, THE Crash_Game SHALL return an error message explaining why the action is invalid
4. WHEN a system error occurs, THE Crash_Game SHALL log the error details and return a generic error message to the player
5. THE Crash_Game SHALL not expose sensitive system information in error messages
