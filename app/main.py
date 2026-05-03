from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import OpenAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
import logging

from app.database import engine, Base
from app.controllers.item_controller import router as items_router
from app.controllers.auth_controller import router as auth_router
from app.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем, включена ли документация (только для development)
is_development = settings.APP_ENV != "production"
docs_url = "/api/docs" if is_development else None
redoc_url = "/api/redoc" if is_development else None

app = FastAPI(
    title="WP Labs API - Лабораторная работа №4",
    description="""
REST API с аутентификацией, авторизацией, OAuth 2.0 и JWT.

## Функциональность:
- **Регистрация и вход** с JWT токенами в HttpOnly cookies
- **OAuth 2.0** через Yandex и VK
- **CRUD операции** с элементами (Items)
- **Soft Delete** для ресурсов
- **Сброс пароля** через email-токен
- **Управление сессиями** (отзыв токенов, logout all)

## Безопасность:
- Пароли хешируются с использованием bcrypt с уникальной солью
- JWT токены передаются через HttpOnly cookies (защита от XSS)
- Защита от CSRF через SameSite cookies
- Проверка владения ресурсами

## Режимы работы:
- **Development**: документация доступна на `/api/docs`
- **Production**: документация отключена (404)
""",
    version="4.0.0",
    docs_url=docs_url,  # Отключаем в production
    redoc_url=redoc_url,  # Отключаем в production
    openapi_tags=[
        {
            "name": "auth",
            "description": "Операции аутентификации и авторизации. Включает регистрацию, вход, OAuth 2.0, управление сессиями и сброс пароля."
        },
        {
            "name": "items",
            "description": "CRUD операции с элементами. Все операции кроме GET требуют авторизации. Пользователи могут управлять только своими элементами."
        },
        {
            "name": "health",
            "description": "Проверка состояния сервера (Health Check)"
        }
    ]
)

# Настраиваем схему безопасности JWT Bearer для Swagger UI
security_scheme = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Введите JWT токен для авторизации. Токен можно получить через POST /auth/login"
)

# Настраиваем CORS для работы с cookies (важно для фронтенда!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4200", "http://127.0.0.1:3000", "http://127.0.0.1:4200"],  # Фронтенд адреса
    allow_credentials=True,  # Разрешаем передачу cookies
    allow_methods=["*"],  # Разрешаем все методы (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Подключаем роутеры (сначала auth, чтобы был доступен /health без аутентификации)
app.include_router(auth_router)
app.include_router(items_router)

# Обработчики ошибок
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработка ошибок валидации (400 Bad Request)"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request data", "errors": exc.errors()}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработка HTTP ошибок (404 Not Found и другие)"""
    logger.warning(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Обработка конфликтов данных (409 Conflict)"""
    logger.error(f"Integrity error: {exc}")
    return JSONResponse(
        status_code=409,
        content={"detail": "Data conflict"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработка внутренних ошибок сервера (500)"""
    logger.error(f"Internal error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check для Docker
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}

# Кастомная OpenAPI схема с настройкой безопасности
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Добавляем схемы безопасности
    openapi_schema["components"]["securitySchemes"] = {
        "JWT Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer токен для авторизации. Получите токен через POST /auth/login и вставьте его сюда."
        },
        "Cookie Auth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "Аутентификация через HttpOnly cookie access_token. При использовании Swagger UI на том же домене cookies отправляются автоматически."
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Запуск только если файл запущен напрямую
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4200)