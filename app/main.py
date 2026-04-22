from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
import logging

from app.database import engine, Base
from app.controllers.item_controller import router as items_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WP Labs API",
    description="Лабораторная работа №2: REST API с PostgreSQL, ORM, Soft Delete и пагинацией",
    version="1.0.0"
)

# Подключаем роутеры
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
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Запуск только если файл запущен напрямую
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4200)