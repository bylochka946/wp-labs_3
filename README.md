# Лабораторная работа №2
## Тема: Проектирование и реализация RESTful API

### Запуск приложения

#### 1. Клонирование репозитория
```bash
git clone https://github.com/bylochka946/wp-labs.git
cd wp-labs
```

#### 2. Настройка окружения

**Windows**
```bash 
copy .env.example .env
```

**Linux/macOS**
```bash 
cp .env.example .env
```

#### 3. Запуск через Docker Compose
```bash 
docker-compose up --build
```
Приложение доступно: http://localhost:4200

#### 4. Проверка
- **Health Check:** http://localhost:4200/health
- **API Docs:** http://localhost:4200/docs

#### 5. Остановка
```bash 
docker-compose down
```

### Переменные окружения
Файл .env.example:
```env
DB_USER=student
DB_PASSWORD=student_secure_password
DB_NAME=wp_labs
DB_HOST=localhost
DB_PORT=5432
```

- **DB_USER**	- Пользователь БД (по умолчанию student)
- **DB_PASSWORD**	- Пароль БД (по умолчанию student_secure_password)
- **DB_NAME**	- Имя базы данных (по умолчанию wp_labs)
- **DB_HOST**	- Хост БД (по умолчанию localhost)
- **DB_PORT** - Порт БД (по умолчанию 5432)

### API Документация
Базовый URL: http://localhost:4200

#### Эндпоинты
- **GET** -	/health	(Проверка работоспособности)
- **POST** -	/items	(Создать элемент)
- **GET** - /items	(Получить список элементов)
- **PUT** - /items/{id}	(Полное обновление элемента)
- **PATCH** - /items/{id} (Частичное обновление элемента)
- **DELETE** - /items/{id}	(Мягкое удаление элемента)

#### Параметры пагинации (для GET /items)
- **page**(integer)	- Номер страницы (от 1, по умолчанию - 1)
- **limit**(integer) - Записей на странице (1-100, по умолчанию - 10)

#### Пример запросов
**POST /items** - Создание элемента:
```json
{
  "name": "Название",
  "description": "Описание",
  "status": "active"
}
```

**GET /items?page=1&limit=10** - Ответ:
```json
{
  "data": [...],
  "meta": {
    "total": 50,
    "page": 1,
    "limit": 10,
    "totalPages": 5
  }
}
```

#### Обработка ошибок
- **400** - Неверный формат данных
- **404** -	Ресурс не найден (или удален)
- **409** -	Конфликт данных
- **500** -	Внутренняя ошибка сервера

### Миграции базы данных
#### Автоматический запуск
Миграции запускаются автоматически при старте контейнера.

#### Ручной запуск
```bash
# Применить все миграции
docker-compose run --rm app alembic upgrade head

# Создать новую миграцию
docker-compose run --rm app alembic revision --autogenerate -m "описание"

# Откатить последнюю миграцию
docker-compose run --rm app alembic downgrade -1
```