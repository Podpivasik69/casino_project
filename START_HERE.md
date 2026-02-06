# 🎰 START HERE - Быстрый старт

## 👋 Добро пожаловать в SKET CASINO MVP!

Это полноценный MVP онлайн-казино с игрой Mines. Все готово к запуску!

## ⚡ Запуск за 60 секунд

```bash
# 1. Запустите сервер
python manage.py runserver

# 2. Откройте браузер
http://127.0.0.1:8000/

# 3. Зарегистрируйтесь и играйте!
```

Вот и все! 🎉

## 📚 Что читать дальше?

### Если вы пользователь
👉 **[QUICKSTART.md](QUICKSTART.md)** - Как играть в Mines

### Если вы разработчик
👉 **[README_MVP.md](README_MVP.md)** - Полная документация  
👉 **[MVP_COMPLETE.md](MVP_COMPLETE.md)** - Что реализовано  
👉 **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Итоговый отчет

### Если вы хотите развивать проект
👉 **[NEXT_STEPS.md](NEXT_STEPS.md)** - Следующие шаги  
👉 **[PRODUCTION_READY.md](PRODUCTION_READY.md)** - Запуск в production

### Если вы хотите демонстрировать
👉 **[DEMO_GUIDE.md](DEMO_GUIDE.md)** - Гайд по демонстрации

## 🎮 Что можно делать?

### Для пользователей
- ✅ Регистрация и вход
- ✅ Получить 1000 ₽ стартового баланса
- ✅ Играть в Mines (5x5, 3-20 мин)
- ✅ Выигрывать до 250x
- ✅ Пополнять демо-баланс (+500 ₽)
- ✅ Смотреть историю транзакций
- ✅ Проверять Provably Fair

### Для разработчиков
- ✅ REST API (14 endpoints)
- ✅ Тесты (95+ тестов)
- ✅ Документация (100%)
- ✅ Чистый код (SOLID)
- ✅ Production-ready

## 🗂️ Структура документации

```
📁 Документация
├── START_HERE.md              ← ВЫ ЗДЕСЬ
├── QUICKSTART.md              ← Быстрый старт для пользователей
├── README_MVP.md              ← Полное руководство
├── MVP_COMPLETE.md            ← Что реализовано
├── PROJECT_SUMMARY.md         ← Итоговый отчет
├── NEXT_STEPS.md              ← Следующие шаги
├── DEMO_GUIDE.md              ← Гайд по демонстрации
├── PRODUCTION_READY.md        ← Production deployment
└── docs/
    ├── auth_service_usage.md  ← AuthService API
    ├── provably_fair_usage.md ← Provably Fair алгоритм
    ├── mines_api_usage.md     ← Mines API
    └── api_examples.md        ← Примеры API
```

## 🎯 Быстрые ссылки

### Страницы
- **Главная**: http://127.0.0.1:8000/
- **Регистрация**: http://127.0.0.1:8000/register/
- **Вход**: http://127.0.0.1:8000/login/
- **Mines**: http://127.0.0.1:8000/mines/
- **Профиль**: http://127.0.0.1:8000/profile/
- **Admin**: http://127.0.0.1:8000/admin/

### API
- **Auth**: http://127.0.0.1:8000/api/auth/
- **Wallet**: http://127.0.0.1:8000/api/wallet/
- **Games**: http://127.0.0.1:8000/api/games/

## 🧪 Тестирование

```bash
# Все тесты
python test_auth_service.py
python test_wallet_service.py
python test_provably_fair.py
python test_mines_service.py
python test_auth_api.py
python test_wallet_api.py
python test_mines_api.py

# Полный MVP тест
python test_mvp.py
```

## 🆘 Проблемы?

### Сервер не запускается
```bash
python manage.py migrate
```

### Ошибка при регистрации
- Пароль должен содержать буквы И цифры (минимум 8 символов)
- Имя пользователя должно быть уникальным

### Не работает игра
- Проверьте баланс (должно быть >= ставки)
- Обновите страницу (F5)

## 📞 Контакты

Если нужна помощь:
1. Прочитайте документацию
2. Проверьте логи
3. Запустите тесты
4. Создайте issue на GitHub

## 🎉 Готово!

Теперь вы знаете, с чего начать. Выберите свой путь:

- 🎮 **Играть** → [QUICKSTART.md](QUICKSTART.md)
- 💻 **Разрабатывать** → [README_MVP.md](README_MVP.md)
- 🚀 **Запускать** → [PRODUCTION_READY.md](PRODUCTION_READY.md)
- 📊 **Демонстрировать** → [DEMO_GUIDE.md](DEMO_GUIDE.md)

---

**Приятной работы! 🚀💎**
