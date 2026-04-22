FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запускаем миграции, потом приложение
CMD ["sh", "-c", "alembic upgrade head && python -m app.main"]