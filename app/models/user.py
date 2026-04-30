from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    # Уникальный идентификатор пользователя
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Контактные данные (email для входа)
    email = Column(String, unique=True, nullable=False, index=True)
    
    # Безопасное хранение пароля
    password_hash = Column(String, nullable=True)  # Может быть NULL для OAuth пользователей
    password_salt = Column(String, nullable=True)  # Соль для хеширования
    
    # OAuth идентификаторы (для входа через сторонние сервисы)
    yandex_id = Column(String, unique=True, nullable=True, index=True)
    vk_id = Column(String, unique=True, nullable=True, index=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Поле для мягкого удаления (Soft Delete)
    deleted_at = Column(DateTime, nullable=True)
    
    def mark_as_deleted(self):
        """Метод для мягкого удаления"""
        self.deleted_at = datetime.utcnow()
    
    @property
    def is_deleted(self) -> bool:
        """Проверка, удалён ли пользователь"""
        return self.deleted_at is not None
    
    def has_password(self) -> bool:
        """Проверяет, установлен ли пароль у пользователя"""
        return self.password_hash is not None
