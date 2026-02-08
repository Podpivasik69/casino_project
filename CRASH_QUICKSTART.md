# Crash Game - Quick Start Guide

## Запуск игры

### 1. Инициализация первого раунда

```bash
.venv\Scripts\activate
python init_crash.py
```

### 2. Запуск сервера

```bash
.venv\Scripts\activate
python manage.py runserver
```

### 3. Открыть игру

Перейти на: http://localhost:8000/crash/

## Автоматическое управление раундами (опционально)

Для автоматического управления раундами запустите в отдельном терминале:

```bash
.venv\Scripts\activate
python manage.py run_crash_rounds
```

Это будет:
- Автоматически активировать раунды после ожидания
- Обрабатывать авто-кэшауты
- Крашить раунды при достижении crash_point
- Создавать новые раунды

## Ручное управление раундами

Если не хотите запускать автоматический менеджер, можно управлять раундами вручную через Django shell:

```python
from games.services.crash_service import CrashGameService
from games.models import CrashRound

# Получить текущий раунд
round = CrashGameService.get_current_round()

# Активировать раунд (если в статусе WAITING)
if round.is_waiting():
    CrashGameService.activate_round(round)

# Крашнуть раунд (если в статусе ACTIVE)
if round.is_active():
    CrashGameService.crash_round(round)

# Создать новый раунд
new_round = CrashGameService.start_new_round()
```

## Как играть

1. **Ожидание раунда**: Раунд в статусе WAITING, показывается обратный отсчет
2. **Размещение ставки**: Введите сумму (0.01 - 1000 ₽) и опционально авто-кэшаут
3. **Активный раунд**: Множитель растет от 1.00x
4. **Кэшаут**: Нажмите "Забрать" чтобы забрать выигрыш
5. **Краш**: Если не успели забрать - ставка проиграна

## Особенности

- **Минимальная ставка**: 0.01 ₽
- **Максимальная ставка**: 1000 ₽
- **Максимум ставок на раунд**: 5 на пользователя
- **Авто-кэшаут**: Минимум 1.01x
- **RTP**: 97% (3% house edge)
- **Обновление множителя**: Каждые 100мс

## Troubleshooting

### Ошибка "Нет активного раунда"

Запустите `python init_crash.py` чтобы создать первый раунд.

### Раунд не активируется автоматически

Запустите `python manage.py run_crash_rounds` в отдельном терминале.

### Множитель не обновляется

Проверьте что:
1. Раунд в статусе ACTIVE
2. JavaScript polling работает (проверьте консоль браузера)
3. API endpoint `/api/games/crash/current/` отвечает

## API Endpoints

- `GET /api/games/crash/current/` - текущий раунд
- `POST /api/games/crash/bet/` - разместить ставку
- `POST /api/games/crash/cashout/` - забрать выигрыш
- `GET /api/games/crash/history/` - история раундов

Подробная документация: `docs/crash_api_usage.md`
