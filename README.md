# Лабораторная работа №4
## Тема: Автоматизированное документирование REST API с использованием OpenAPI (Swagger)

### Краткое описание проекта

REST API с полной автоматизированной документацией OpenAPI (Swagger):
- **Автоматическая генерация** документации из кода (Code-First подход)
- **Интерактивный Swagger UI** для тестирования API endpoints
- **JWT аутентификация** через HttpOnly cookies с поддержкой в Swagger UI
- **OAuth 2.0** через российские провайдеры (Yandex, VK)
- **CRUD операции** с элементами (Items) с проверкой владения
- **Soft Delete** для ресурсов
- **Сброс пароля** через email-токен
- **Управление сессиями** (отзыв токенов, logout all)
- **Разделение конфигурации** для development/production режимов
- Технологии: Python 3.11, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16, Docker

### Документация API

#### Режим разработки (Development)
При `APP_ENV=development` документация доступна по адресу:
- **Swagger UI**: http://localhost:4200/api/docs
- **ReDoc**: http://localhost:4200/api/redoc

#### Промышленный режим (Production)
При `APP_ENV=production` документация **отключена** (возвращает 404 Not Found).

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

## Использование Swagger UI для тестирования API

### 1. Запуск приложения в режиме разработки

```bash
# Убедитесь, что в .env файле:
APP_ENV=development

# Запуск через Docker
docker-compose up --build
```

### 2. Открытие документации

Перейдите в браузере на: http://localhost:4200/api/docs

### 3. Тестирование защищенных endpoints

#### Вариант A: Автоматическая аутентификация через cookies

1. В Swagger UI выполните `POST /auth/login` с email и паролем
2. Токены автоматически сохранятся в cookies браузера
3. Все последующие запросы из Swagger UI будут использовать эти cookies

#### Вариант B: Ручной ввод JWT токена

1. Выполните `POST /auth/login` через curl или другой клиент
2. Извлеките access_token из cookies ответа
3. В Swagger UI нажмите кнопку "Authorize" (значок замка)
4. Введите токен в формате: `Bearer <your_token>`
5. Нажмите "Authorize"

### 4. Тестирование защищенных операций

После аутентификации вы можете тестировать:
- `GET /auth/whoami` - проверка авторизации
- `POST /items` - создание элемента
- `GET /items` - получение списка элементов
- `PUT /items/{id}` - полное обновление
- `PATCH /items/{id}` - частичное обновление
- `DELETE /items/{id}` - мягкое удаление

### 5. Переключение в production режим

```bash
# Измените в .env:
APP_ENV=production

# Перезапустите приложение
docker-compose down
docker-compose up --build
```

Теперь при попытке доступа к `/api/docs` вы получите **404 Not Found**.


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

https://passport.yandex.ru/profile

http://localhost:4200/auth/oauth/yandex

http://localhost:4200/auth/oauth/yandex/callback