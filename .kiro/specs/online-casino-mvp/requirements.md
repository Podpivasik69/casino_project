# Requirements Document

## Introduction

Данный документ описывает требования к MVP онлайн-казино на Django с двумя играми (Mines и Plinko). Система работает в демо-режиме без реальных денег, использует SQLite и следует принципам SOLID/SRP. Основная цель - создать функциональное казино с системой аутентификации, виртуальным кошельком и двумя играми с Provably Fair алгоритмами.

## Glossary

- **System**: Django-приложение онлайн-казино
- **User**: Зарегистрированный пользователь системы
- **Profile**: Профиль пользователя с балансом
- **Wallet_Service**: Сервис для операций с балансом
- **Transaction**: Запись о финансовой операции (депозит/ставка/выигрыш)
- **Mines_Game**: Игра с полем 5x5 и скрытыми минами
- **Plinko_Game**: Игра с падающим шариком через ряды колышков
- **Provably_Fair**: Алгоритм проверяемой честности (HMAC-SHA256)
- **Demo_Balance**: Виртуальный баланс для демо-режима
- **RTP**: Return to Player - процент возврата игроку (~97%)
- **Multiplier**: Множитель выигрыша
- **Cashout**: Действие забрать выигрыш

## Requirements

### Requirement 1: User Authentication System

**User Story:** As a user, I want to register, login, and logout, so that I can access my personal account and game history.

#### Acceptance Criteria

1. WHEN a user submits valid registration data (username, email, password), THE System SHALL create a new User account and Profile with initial demo balance
2. WHEN a user submits registration data with an existing username or email, THE System SHALL reject the registration and return a descriptive error
3. WHEN a user submits valid login credentials, THE System SHALL authenticate the user and create a session
4. WHEN a user submits invalid login credentials, THE System SHALL reject the login and return an authentication error
5. WHEN an authenticated user requests logout, THE System SHALL terminate the session and redirect to the login page
6. THE System SHALL validate all user input data (username length, email format, password strength)
7. THE System SHALL protect against CSRF attacks on authentication endpoints

### Requirement 2: User Profile Management

**User Story:** As a user, I want to view and manage my profile, so that I can see my balance and account information.

#### Acceptance Criteria

1. WHEN a user accesses their profile page, THE System SHALL display username, email, current balance, and registration date
2. WHEN a Profile is created, THE System SHALL initialize it with a default demo balance
3. THE System SHALL maintain a one-to-one relationship between User and Profile
4. WHEN a user's balance changes, THE System SHALL update the Profile balance atomically
5. THE System SHALL prevent negative balance values in Profile

### Requirement 3: Wallet Transaction System

**User Story:** As a user, I want to manage my demo balance and view transaction history, so that I can track my deposits, bets, and winnings.

#### Acceptance Criteria

1. WHEN a user requests a demo deposit, THE System SHALL add a fixed amount to their balance and create a Transaction record with type "deposit"
2. WHEN a user places a bet, THE Wallet_Service SHALL deduct the bet amount from balance and create a Transaction record with type "bet"
3. WHEN a user wins, THE Wallet_Service SHALL add the winning amount to balance and create a Transaction record with type "win"
4. WHEN a user requests transaction history, THE System SHALL return all transactions ordered by timestamp descending
5. THE Wallet_Service SHALL ensure all balance operations are atomic and prevent race conditions
6. WHEN a user attempts to bet more than their current balance, THE Wallet_Service SHALL reject the operation and return an insufficient funds error
7. THE System SHALL log all wallet operations for audit purposes

### Requirement 4: Mines Game Core Logic

**User Story:** As a player, I want to play Mines game with provably fair mechanics, so that I can trust the game outcomes and enjoy strategic gameplay.

#### Acceptance Criteria

1. WHEN a user starts a new Mines game with valid bet amount and mine count (3-20), THE System SHALL create a Mines_Game instance with randomly placed mines using Provably_Fair algorithm
2. WHEN a Mines_Game is created, THE System SHALL generate a server seed, client seed, and nonce for Provably_Fair verification
3. WHEN a user opens a safe cell, THE System SHALL reveal the cell, increase the current multiplier, and allow continued play
4. WHEN a user opens a cell with a mine, THE System SHALL end the game, reveal all mines, and the user loses their bet
5. WHEN a user requests cashout, THE System SHALL calculate winnings (bet × current multiplier), add to balance, end the game, and reveal all cells
6. THE System SHALL enforce maximum multiplier of 504x for Mines game
7. WHEN a user requests game verification, THE System SHALL provide server seed, client seed, nonce, and allow verification of mine positions
8. THE System SHALL prevent opening cells after game has ended (win/loss/cashout)
9. THE System SHALL prevent opening the same cell twice

### Requirement 5: Plinko Game Core Logic

**User Story:** As a player, I want to play Plinko game with different risk levels, so that I can choose my preferred risk-reward balance.

#### Acceptance Criteria

1. WHEN a user starts a new Plinko game with valid bet amount, row count (12-16), and risk level (Low/Medium/High), THE System SHALL create a Plinko_Game instance
2. WHEN a ball is dropped, THE System SHALL simulate random walk through rows and determine final multiplier bucket
3. WHEN a ball lands in a bucket, THE System SHALL calculate winnings (bet × bucket multiplier) and add to user balance
4. THE System SHALL enforce maximum multiplier of 555x for Plinko game
5. WHERE risk level is Low, THE System SHALL use low-risk multiplier distribution
6. WHERE risk level is Medium, THE System SHALL use medium-risk multiplier distribution
7. WHERE risk level is High, THE System SHALL use high-risk multiplier distribution
8. WHEN auto-play is enabled, THE System SHALL execute multiple drops sequentially until count is reached or balance is insufficient
9. THE System SHALL maintain RTP of approximately 97% across all risk levels

### Requirement 6: Provably Fair Implementation

**User Story:** As a player, I want to verify game fairness, so that I can trust that outcomes are not manipulated.

#### Acceptance Criteria

1. WHEN a game is created, THE System SHALL generate a cryptographically secure server seed
2. THE System SHALL allow users to provide a client seed or generate one automatically
3. THE System SHALL use HMAC-SHA256 algorithm to combine server seed, client seed, and nonce for outcome generation
4. WHEN a game ends, THE System SHALL reveal the server seed for verification
5. THE System SHALL provide verification endpoint that accepts seeds and nonce and returns the same outcome
6. THE System SHALL ensure server seed is not revealed before game completion

### Requirement 7: API Endpoints for Authentication

**User Story:** As a frontend developer, I want RESTful API endpoints for authentication, so that I can build a responsive user interface.

#### Acceptance Criteria

1. THE System SHALL provide POST /api/auth/register endpoint that accepts username, email, password and returns user data or validation errors
2. THE System SHALL provide POST /api/auth/login endpoint that accepts credentials and returns authentication token or error
3. THE System SHALL provide POST /api/auth/logout endpoint that terminates the session
4. THE System SHALL provide GET /api/auth/me endpoint that returns current authenticated user data
5. THE System SHALL return appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 500)
6. THE System SHALL return JSON responses with consistent structure

### Requirement 8: API Endpoints for Wallet

**User Story:** As a frontend developer, I want API endpoints for wallet operations, so that users can manage their balance.

#### Acceptance Criteria

1. THE System SHALL provide GET /api/wallet/balance endpoint that returns current user balance
2. THE System SHALL provide POST /api/wallet/deposit endpoint that adds demo funds to user balance
3. THE System SHALL provide GET /api/wallet/transactions endpoint that returns paginated transaction history
4. WHEN wallet endpoints are accessed without authentication, THE System SHALL return 401 Unauthorized
5. THE System SHALL validate all wallet operation amounts are positive numbers

### Requirement 9: API Endpoints for Mines Game

**User Story:** As a frontend developer, I want API endpoints for Mines game, so that users can play the game.

#### Acceptance Criteria

1. THE System SHALL provide POST /api/games/mines/new endpoint that accepts bet amount and mine count and returns game instance
2. THE System SHALL provide POST /api/games/mines/{id}/open endpoint that accepts cell coordinates and returns cell state and updated game state
3. THE System SHALL provide POST /api/games/mines/{id}/cashout endpoint that processes cashout and returns final winnings
4. THE System SHALL provide GET /api/games/mines/{id}/verify endpoint that returns provably fair verification data
5. WHEN game endpoints are accessed for non-existent game, THE System SHALL return 404 Not Found
6. WHEN game endpoints are accessed by non-owner user, THE System SHALL return 403 Forbidden

### Requirement 10: API Endpoints for Plinko Game

**User Story:** As a frontend developer, I want API endpoints for Plinko game, so that users can play the game.

#### Acceptance Criteria

1. THE System SHALL provide POST /api/games/plinko/new endpoint that accepts bet amount, row count, and risk level and returns game instance
2. THE System SHALL provide POST /api/games/plinko/{id}/drop endpoint that simulates ball drop and returns path and winnings
3. THE System SHALL provide POST /api/games/plinko/auto endpoint that accepts bet parameters and drop count for auto-play
4. WHEN Plinko endpoints receive invalid risk level, THE System SHALL return 400 Bad Request with validation error
5. WHEN Plinko endpoints receive invalid row count (not 12-16), THE System SHALL return 400 Bad Request

### Requirement 11: Frontend Templates

**User Story:** As a user, I want intuitive web pages, so that I can easily navigate and play games.

#### Acceptance Criteria

1. THE System SHALL provide a base template with navigation, user info, and balance display
2. THE System SHALL provide registration and login pages with form validation
3. THE System SHALL provide a profile page displaying user information and transaction history
4. THE System SHALL provide a Mines game page with 5x5 grid interface
5. THE System SHALL provide a Plinko game page with visual representation of rows and buckets
6. WHEN a user is not authenticated, THE System SHALL redirect game pages to login
7. THE System SHALL display real-time balance updates after each transaction

### Requirement 12: Security and Validation

**User Story:** As a system administrator, I want robust security measures, so that the application is protected from common vulnerabilities.

#### Acceptance Criteria

1. THE System SHALL implement CSRF protection on all state-changing endpoints
2. THE System SHALL sanitize all user inputs to prevent XSS attacks
3. THE System SHALL use Django's built-in password hashing for user passwords
4. THE System SHALL validate all numeric inputs (bet amounts, mine counts, row counts) are within allowed ranges
5. THE System SHALL implement rate limiting on authentication endpoints to prevent brute force attacks
6. THE System SHALL log all security-relevant events (failed logins, invalid operations)
7. THE System SHALL use HTTPS in production environment

### Requirement 13: Database Models and Relationships

**User Story:** As a developer, I want well-structured database models, so that data integrity is maintained.

#### Acceptance Criteria

1. THE System SHALL extend Django's AbstractUser for User model
2. THE System SHALL create Profile model with OneToOneField to User and balance field
3. THE System SHALL create Transaction model with ForeignKey to User, amount, transaction_type, and timestamp
4. THE System SHALL create MinesGame model with ForeignKey to User, bet_amount, mine_count, game_state, and provably fair fields
5. THE System SHALL create PlinkoGame model with ForeignKey to User, bet_amount, row_count, risk_level, and result fields
6. THE System SHALL use database constraints to ensure data integrity (non-negative balances, valid enums)
7. THE System SHALL create appropriate database indexes for frequently queried fields

### Requirement 14: Service Layer Architecture

**User Story:** As a developer, I want a clean service layer, so that business logic is separated from views and models.

#### Acceptance Criteria

1. THE System SHALL implement Wallet_Service with methods for deposit, bet, win, and get_balance
2. THE System SHALL implement MinesGameService with methods for create_game, open_cell, cashout, and verify
3. THE System SHALL implement PlinkoGameService with methods for create_game, drop_ball, and auto_play
4. THE System SHALL ensure all business logic resides in service layer, not in views or models
5. THE System SHALL use database transactions in service methods to ensure atomicity
6. THE System SHALL raise appropriate exceptions for business rule violations

### Requirement 15: Logging and Monitoring

**User Story:** As a system administrator, I want comprehensive logging, so that I can monitor system health and debug issues.

#### Acceptance Criteria

1. THE System SHALL log all game creations with user, game type, and bet amount
2. THE System SHALL log all wallet operations with user, operation type, and amount
3. THE System SHALL log all authentication events (login, logout, failed attempts)
4. THE System SHALL log all errors with stack traces
5. THE System SHALL use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
6. THE System SHALL configure logging to write to both console and file in production

### Requirement 16: Configuration and Settings

**User Story:** As a developer, I want proper Django configuration, so that the application runs correctly in different environments.

#### Acceptance Criteria

1. THE System SHALL configure SQLite as the database backend for MVP
2. THE System SHALL set appropriate SECRET_KEY for production
3. THE System SHALL configure ALLOWED_HOSTS for production deployment
4. THE System SHALL enable Django's security middleware (CSRF, XSS protection)
5. THE System SHALL configure static files and media files handling
6. THE System SHALL set DEBUG=False in production
7. THE System SHALL configure session timeout for user sessions

### Requirement 17: URL Routing

**User Story:** As a developer, I want organized URL routing, so that endpoints are logical and maintainable.

#### Acceptance Criteria

1. THE System SHALL organize URLs by application (users, wallet, games)
2. THE System SHALL use Django's path() and include() for URL configuration
3. THE System SHALL namespace API URLs under /api/ prefix
4. THE System SHALL use RESTful URL patterns for resources
5. THE System SHALL provide URL names for reverse URL resolution

### Requirement 18: Game RTP and Balance

**User Story:** As a casino operator, I want games to maintain target RTP, so that the casino remains profitable while fair to players.

#### Acceptance Criteria

1. THE System SHALL configure Mines multipliers to achieve approximately 97% RTP
2. THE System SHALL configure Plinko multipliers for each risk level to achieve approximately 97% RTP
3. WHEN calculating multipliers, THE System SHALL use mathematically sound probability distributions
4. THE System SHALL document RTP calculations in code comments

### Requirement 19: Error Handling

**User Story:** As a user, I want clear error messages, so that I understand what went wrong and how to fix it.

#### Acceptance Criteria

1. WHEN validation fails, THE System SHALL return specific error messages indicating which field is invalid
2. WHEN insufficient balance occurs, THE System SHALL return error message with current balance and required amount
3. WHEN game state is invalid for operation, THE System SHALL return error explaining the issue
4. THE System SHALL never expose internal system details in error messages
5. THE System SHALL return user-friendly error messages in Russian language

### Requirement 20: Initial Data and Fixtures

**User Story:** As a developer, I want initial data setup, so that I can quickly test the application.

#### Acceptance Criteria

1. THE System SHALL provide management command to create demo users
2. THE System SHALL provide initial demo balance for new users
3. THE System SHALL include database migrations for all models
4. THE System SHALL provide fixtures for testing game configurations
