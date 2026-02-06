# 🚀 Production Deployment Guide

## Что нужно изменить для production

### 1. Settings (casino/settings.py)

```python
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')  # Из переменных окружения

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Security Settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/casino/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### 2. Requirements для production

```txt
# requirements_prod.txt
Django==5.0.2
psycopg2-binary==2.9.9
gunicorn==21.2.0
whitenoise==6.6.0
redis==5.0.1
celery==5.3.4
django-redis==5.4.0
sentry-sdk==1.39.1
```

### 3. Gunicorn конфигурация

```python
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
loglevel = "info"
```

### 4. Nginx конфигурация

```nginx
# /etc/nginx/sites-available/casino
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /static/ {
        alias /var/www/casino/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Systemd service

```ini
# /etc/systemd/system/casino.service
[Unit]
Description=Casino Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/casino
Environment="PATH=/var/www/casino/venv/bin"
ExecStart=/var/www/casino/venv/bin/gunicorn \
    --config /var/www/casino/gunicorn_config.py \
    casino.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 6. Docker (опционально)

```dockerfile
# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_prod.txt .
RUN pip install --no-cache-dir -r requirements_prod.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn_config.py", "casino.wsgi:application"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: casino
      POSTGRES_USER: casino_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  web:
    build: .
    command: gunicorn --config gunicorn_config.py casino.wsgi:application
    volumes:
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/var/www/static
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
```

### 7. Environment Variables

```bash
# .env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_NAME=casino
DB_USER=casino_user
DB_PASSWORD=your-db-password
DB_HOST=db
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

REDIS_URL=redis://redis:6379/0

SENTRY_DSN=your-sentry-dsn
```

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Все тесты проходят
- [ ] Код в git репозитории
- [ ] Environment variables настроены
- [ ] SSL сертификат получен
- [ ] Домен настроен
- [ ] Сервер подготовлен

### Deployment
- [ ] PostgreSQL установлен и настроен
- [ ] Redis установлен (для кеширования)
- [ ] Nginx установлен и настроен
- [ ] Python venv создан
- [ ] Dependencies установлены
- [ ] Migrations применены
- [ ] Static files собраны
- [ ] Gunicorn настроен
- [ ] Systemd service создан
- [ ] Firewall настроен

### Post-deployment
- [ ] Сайт доступен по HTTPS
- [ ] Все страницы работают
- [ ] API endpoints работают
- [ ] Логи настроены
- [ ] Мониторинг настроен
- [ ] Backup настроен
- [ ] Документация обновлена

## 🔧 Deployment Commands

```bash
# 1. Подготовка сервера (Ubuntu 22.04)
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql nginx redis-server

# 2. Создание пользователя и директории
sudo useradd -m -s /bin/bash casino
sudo mkdir -p /var/www/casino
sudo chown casino:casino /var/www/casino

# 3. Клонирование репозитория
cd /var/www/casino
git clone https://github.com/yourusername/casino.git .

# 4. Создание virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 5. Установка зависимостей
pip install -r requirements_prod.txt

# 6. Настройка PostgreSQL
sudo -u postgres psql
CREATE DATABASE casino;
CREATE USER casino_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE casino TO casino_user;
\q

# 7. Применение миграций
python manage.py migrate

# 8. Создание суперпользователя
python manage.py createsuperuser

# 9. Сбор статических файлов
python manage.py collectstatic --noinput

# 10. Настройка Gunicorn
sudo cp gunicorn_config.py /var/www/casino/
sudo cp casino.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start casino
sudo systemctl enable casino

# 11. Настройка Nginx
sudo cp nginx.conf /etc/nginx/sites-available/casino
sudo ln -s /etc/nginx/sites-available/casino /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 12. Получение SSL сертификата
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 13. Настройка firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

## 📊 Мониторинг

### 1. Sentry для отслеживания ошибок

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

### 2. Prometheus + Grafana

```python
# requirements_prod.txt
django-prometheus==2.3.1
```

```python
# settings.py
INSTALLED_APPS = [
    'django_prometheus',
    # ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

### 3. Логирование

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/casino/django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

## 🔐 Безопасность

### 1. Регулярные обновления
```bash
# Обновление зависимостей
pip list --outdated
pip install --upgrade package-name
```

### 2. Backup базы данных
```bash
# Создание backup
pg_dump casino > backup_$(date +%Y%m%d).sql

# Восстановление
psql casino < backup_20260206.sql
```

### 3. Rate limiting
```python
# settings.py
INSTALLED_APPS = [
    'django_ratelimit',
    # ...
]

# views.py
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m')
def login_view(request):
    # ...
```

## 📈 Масштабирование

### 1. Redis для кеширования
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 2. Celery для фоновых задач
```python
# celery.py
from celery import Celery

app = Celery('casino')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### 3. CDN для статических файлов
```python
# settings.py
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
```

## 🎯 Performance Optimization

### 1. Database indexes
```python
# models.py
class Transaction(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
        ]
```

### 2. Query optimization
```python
# views.py
# Используйте select_related и prefetch_related
transactions = Transaction.objects.select_related('user').all()
```

### 3. Caching
```python
# views.py
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 минут
def home_view(request):
    # ...
```

## 📝 Maintenance

### Регулярные задачи
- [ ] Ежедневный backup базы данных
- [ ] Еженедельная проверка логов
- [ ] Ежемесячное обновление зависимостей
- [ ] Квартальный security audit
- [ ] Годовое обновление SSL сертификата

---

**Production-ready! 🚀**
