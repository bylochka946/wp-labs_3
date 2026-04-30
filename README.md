# Лабораторная работа №2
## Тема: Авторизация и аутентификация (JWT, OAuth2, Cookies)

### Краткое описание проекта

Добавлена система аутентификации и авторизации:
- JWT токены (Access/Refresh) с передачей через HttpOnly cookies
- Безопасное хранение паролей (bcrypt с уникальной солью)
- OAuth 2.0 через российские провайдеры (Yandex, VK)
- Управление сессиями (отзыв токенов, logout all)
- Защита ресурсов с проверкой владения
- Сброс пароля через email-токен
- Технологии: Python 3.11, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16, Docker

### Пример файла переменных окружения (.env.example)

# Database Configuration (PostgreSQL)
DB_USER=student
DB_PASSWORD=student_secure_password
DB_NAME=wp_labs
DB_HOST=localhost
DB_PORT=5432

# JWT Configuration
# Секретные ключи для подписи JWT токенов
JWT_ACCESS_SECRET=super_secret_access_key_change_in_prod
JWT_REFRESH_SECRET=super_secret_refresh_key_change_in_prod

# Время жизни токенов в минутах
JWT_ACCESS_EXPIRATION=15          # 15 минут
JWT_REFRESH_EXPIRATION=10080      # 7 дней 

# OAuth Yandex Configuration
# https://oauth.yandex.ru/
YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_REDIRECT_URI=http://localhost:4200/auth/oauth/yandex/callback


# OAuth VK Configuration
# https://dev.vk.com/
VK_CLIENT_ID=your_vk_client_id
VK_CLIENT_SECRET=your_vk_client_secret
VK_REDIRECT_URI=http://localhost:4200/auth/oauth/vk/callback

#### Примера запросов

POST /auth/register - Регистрация
```bash
curl -X POST http://localhost:4200/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test1@example.com\",\"password\":\"TestPass1234\"}" ^
  -c cookies.txt ^
  -v
```

POST /auth/login - Вход 
```bash
curl -X POST http://localhost:4200/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test1@example.com\",\"password\":\"TestPass1234\"}" ^
  -c cookies.txt ^
  -v
```

GET /auth/whoami - Проверка авторизации
```bash
curl -X GET http://localhost:4200/auth/whoami ^
  -b cookies.txt ^
  -v
```

POST /auth/refresh - Обновление токенов
```bash
curl -X POST http://localhost:4200/auth/refresh ^
  -b cookies.txt ^
  -c cookies.txt ^
  -v
```

POST /auth/logout - Завершение текущей сессии
```bash
curl -X POST http://localhost:4200/auth/logout ^
  -b cookies.txt ^
  -c cookies.txt ^
  -v
```

POST /auth/logout-all - Завершение всех сессий пользователя
```bash
curl -X POST http://localhost:4200/auth/logout-all ^
  -b cookies.txt ^
  -c cookies.txt ^
  -v
```

POST /auth/forgot-password - Запрос сброса пароля
```bash
curl -X POST http://localhost:4200/auth/forgot-password ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test1@example.com\"}" ^
  -v
```

️POST /auth/reset-password - Установка нового пароля
```bash
curl -X POST http://localhost:4200/auth/reset-password ^
  -H "Content-Type: application/json" ^
  -d "{\"token\":\"YOUR_RESET_TOKEN\",\"new_password\":\"NewPass456\"}" ^
  -v
```

GET /auth/oauth/yandex - OAuth инициация
```bash
curl -X GET http://localhost:4200/auth/oauth/yandex ^
```

