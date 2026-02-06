# API Endpoints Specification

## Authentication
- POST /api/auth/register - Регистрация
- POST /api/auth/login - Вход
- POST /api/auth/logout - Выход
- GET /api/auth/me - Текущий пользователь

## Wallet
- GET /api/wallet/balance - Получить баланс
- POST /api/wallet/deposit - Демо-пополнение
- GET /api/wallet/transactions - История транзакций

## Games - Mines
- POST /api/games/mines/new - Новая игра Mines
- POST /api/games/mines/{id}/open - Открыть клетку
- POST /api/games/mines/{id}/cashout - Забрать выигрыш
- GET /api/games/mines/{id}/verify - Проверить честность

## Games - Plinko
- POST /api/games/plinko/new - Новая игра Plinko
- POST /api/games/plinko/{id}/drop - Бросить шарик
- POST /api/games/plinko/auto - Автоигра (N раз)

## Admin
- GET /api/admin/stats - Статистика
- GET /api/admin/users - Список пользователей# Games Logic Specification

## Mines Game
### Configuration:
- Grid: 5x5 (25 cells)
- Mines: 3-20 (user selects)
- RTP: ~97%
- Max multiplier: 504x

### Game Flow:
1. User places bet, selects mines count
2. System generates board with mines
3. User opens cells one by one
4. Multiplier increases per safe cell
5. User can cashout anytime
6. If mine opened -> lose bet

### Provably Fair:
- Server seed (hashed before game)
- Client seed (from user)
- Nonce (game number)
- HMAC-SHA256(server_seed + client_seed + nonce)
- Reveal server seed after game

## Plinko Game
### Configuration:
- Rows: 12-16
- Risk levels: Low(Green), Medium(Yellow), High(Red)
- RTP: ~97%
- Max multiplier: 555x

### Multiplier Distribution:
- Green: 1x-10x (frequent small)
- Yellow: 1x-100x (balanced)
- Red: 1x-555x (rare high)
# Tasks for Kiro Dev (Priority Order)

## Phase 1: Core Setup
1. Configure Django settings for MVP
2. Create User and Profile models
3. Basic authentication (register/login)
4. Wallet service with demo deposit

## Phase 2: Game - Mines
5. Mines domain models
6. Provably Fair RNG implementation
7. Mines game service logic
8. Mines API endpoints
9. Basic frontend for Mines

## Phase 3: Game - Plinko
10. Plinko domain models
11. Plinko physics simulation
12. Plinko game service
13. Plinko API endpoints
14. Frontend for Plinko

## Phase 4: Polish
15. Transaction history
16. Admin interface basics
17. Security validations
18. Testing critical paths

## Rules:
- Follow SOLID principles
- Each file should have single responsibility
- Use service layer for business logic
- Validate all user inputs
- Log important eventsсдуфк
- сжу
### Game Flow:
1. User places bet, selects risk level
2. Ball drops through pegs
3. Final position determines multiplier
4. Win = bet × multiplier
5. Auto-play option available

### Physics:
- Each peg: 50% left, 50% right
- Random walk simulation
- Risk level changes multiplier table