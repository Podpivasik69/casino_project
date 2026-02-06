# Plinko Game API Usage Guide

## Overview

Plinko - это игра, где шарик падает через ряды колышков и приземляется в одну из корзин с множителями. Игра поддерживает три уровня риска (Low, Medium, High) и различное количество рядов (12-16).

## API Endpoints

### 1. Create Plinko Game

Создает новую игру Plinko (без броска шарика).

**Endpoint:** `POST /api/games/plinko/create/`

**Request:**
```json
{
    "bet_amount": "10.00",
    "row_count": 14,
    "risk_level": "medium"
}
```

**Parameters:**
- `bet_amount` (string): Сумма ставки (минимум 0.01)
- `row_count` (integer): Количество рядов (12-16)
- `risk_level` (string): Уровень риска ("low", "medium", "high")

**Response:**
```json
{
    "success": true,
    "game": {
        "id": 1,
        "bet_amount": "10.00",
        "row_count": 14,
        "risk_level": "medium",
        "risk_level_display": "Средний",
        "created_at": "2024-01-01T12:00:00Z"
    }
}
```

### 2. Drop Ball

Бросает шарик в созданной игре.

**Endpoint:** `POST /api/games/plinko/<game_id>/drop/`

**Response:**
```json
{
    "success": true,
    "result": {
        "ball_path": [0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
        "bucket_index": 7,
        "multiplier": "0.40",
        "winnings": "4.00"
    },
    "balance": "1004.00"
}
```

**Result Fields:**
- `ball_path`: Массив 0/1, где 0 = влево, 1 = вправо
- `bucket_index`: Индекс финальной корзины (0 to row_count)
- `multiplier`: Множитель выигрыша
- `winnings`: Сумма выигрыша (bet_amount × multiplier)
- `balance`: Новый баланс пользователя

### 3. Get Game Details

Получает информацию об игре.

**Endpoint:** `GET /api/games/plinko/<game_id>/`

**Response:**
```json
{
    "success": true,
    "game": {
        "id": 1,
        "bet_amount": "10.00",
        "row_count": 14,
        "risk_level": "medium",
        "risk_level_display": "Средний",
        "ball_path": [0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
        "bucket_index": 7,
        "final_multiplier": "0.40",
        "is_completed": true,
        "created_at": "2024-01-01T12:00:00Z"
    }
}
```

### 4. Auto-Play

Выполняет несколько бросков автоматически.

**Endpoint:** `POST /api/games/plinko/auto/`

**Request:**
```json
{
    "bet_amount": "10.00",
    "row_count": 14,
    "risk_level": "medium",
    "drop_count": 10
}
```

**Parameters:**
- `drop_count` (integer): Количество бросков (1-100)

**Response:**
```json
{
    "success": true,
    "results": [
        {
            "game_id": 1,
            "drop_number": 1,
            "ball_path": [0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
            "bucket_index": 7,
            "multiplier": "0.40",
            "winnings": "4.00"
        },
        ...
    ],
    "total_drops": 10,
    "total_winnings": "95.00",
    "balance": "1095.00"
}
```

### 5. Get Multipliers

Получает таблицы множителей для всех уровней риска.

**Endpoint:** `GET /api/games/plinko/multipliers/`

**Response:**
```json
{
    "success": true,
    "multipliers": {
        "low": {
            "12": [8.4, 4.2, 2.1, 1.4, 1.1, 1.0, 1.0, 1.1, 1.4, 2.1, 4.2, 8.4, 16.8],
            "13": [...],
            "14": [...],
            "15": [...],
            "16": [...]
        },
        "medium": {
            "12": [13.0, 6.0, 3.0, 1.5, 1.0, 0.5, 0.3, 0.5, 1.0, 1.5, 3.0, 6.0, 13.0],
            ...
        },
        "high": {
            "12": [29.0, 13.0, 5.0, 2.0, 0.7, 0.2, 0.1, 0.2, 0.7, 2.0, 5.0, 13.0, 29.0],
            ...
        }
    }
}
```

## Multiplier Tables

### Low Risk
- **12 rows**: Max 16.8x
- **13 rows**: Max 26.0x
- **14 rows**: Max 36.0x
- **15 rows**: Max 50.0x
- **16 rows**: Max 70.0x

### Medium Risk
- **12 rows**: Max 13.0x
- **13 rows**: Max 20.0x
- **14 rows**: Max 60.0x
- **15 rows**: Max 86.0x
- **16 rows**: Max 120.0x

### High Risk
- **12 rows**: Max 29.0x
- **13 rows**: Max 43.0x
- **14 rows**: Max 152.0x
- **15 rows**: Max 240.0x
- **16 rows**: Max 555.0x

## Game Flow

1. **Create Game**: Создайте игру с параметрами (ставка, ряды, риск)
2. **Drop Ball**: Бросьте шарик - система симулирует падение
3. **Get Result**: Получите путь шарика, корзину и выигрыш
4. **Repeat**: Создайте новую игру для следующего броска

## Ball Physics

Шарик падает через ряды колышков:
- На каждом ряду: 50% шанс пойти влево (0) или вправо (1)
- Финальная корзина = сумма всех "вправо" (сумма единиц в пути)
- Для 14 рядов: корзины от 0 до 14 (всего 15 корзин)

## Error Handling

### Common Errors

**400 Bad Request:**
```json
{
    "success": false,
    "error": "Количество рядов должно быть от 12 до 16"
}
```

**404 Not Found:**
```json
{
    "success": false,
    "error": "Игра не найдена"
}
```

**400 Insufficient Funds:**
```json
{
    "success": false,
    "error": "Недостаточно средств. Баланс: 5.00 ₽, требуется: 10.00 ₽"
}
```

## Usage Examples

### Python Example

```python
import requests

# Create game
response = requests.post('http://localhost:8000/api/games/plinko/create/', json={
    'bet_amount': '10.00',
    'row_count': 14,
    'risk_level': 'high'
})
game_id = response.json()['game']['id']

# Drop ball
response = requests.post(f'http://localhost:8000/api/games/plinko/{game_id}/drop/')
result = response.json()['result']

print(f"Ball path: {result['ball_path']}")
print(f"Bucket: {result['bucket_index']}")
print(f"Multiplier: {result['multiplier']}x")
print(f"Winnings: {result['winnings']} ₽")
```

### JavaScript Example

```javascript
// Create and drop ball
async function playPlinko() {
    // Create game
    const createResponse = await fetch('/api/games/plinko/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            bet_amount: '10.00',
            row_count: 14,
            risk_level: 'medium'
        })
    });
    const game = await createResponse.json();
    
    // Drop ball
    const dropResponse = await fetch(`/api/games/plinko/${game.game.id}/drop/`, {
        method: 'POST'
    });
    const result = await dropResponse.json();
    
    console.log('Result:', result.result);
}
```

### Auto-Play Example

```python
# Play 10 drops automatically
response = requests.post('http://localhost:8000/api/games/plinko/auto/', json={
    'bet_amount': '10.00',
    'row_count': 16,
    'risk_level': 'high',
    'drop_count': 10
})

data = response.json()
print(f"Total drops: {data['total_drops']}")
print(f"Total winnings: {data['total_winnings']} ₽")
print(f"Final balance: {data['balance']} ₽")

for result in data['results']:
    print(f"Drop {result['drop_number']}: {result['multiplier']}x = {result['winnings']} ₽")
```

## RTP (Return to Player)

Все уровни риска настроены на RTP ~97%:
- **Low Risk**: Более стабильные выплаты, меньше волатильность
- **Medium Risk**: Сбалансированные выплаты
- **High Risk**: Высокая волатильность, большие множители на краях

## Tips

1. **Low Risk**: Подходит для длительной игры с меньшим риском
2. **Medium Risk**: Баланс между риском и наградой
3. **High Risk**: Для игроков, ищущих большие выигрыши
4. **More Rows**: Больше рядов = больше максимальный множитель
5. **Auto-Play**: Используйте для быстрого тестирования стратегий
