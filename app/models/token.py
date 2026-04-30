from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class Token(Base):
    __tablename__ = "tokens"
    
    # Уникальный идентификатор токена
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Связь с пользователем (кто владеет этим токеном)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Хеш токена (храним НЕ сам токен, а его хеш для безопасности)
    token_hash = Column(String, nullable=False, index=True)
    
    # Срок действия токена
    expires_at = Column(DateTime, nullable=False)
    
    # Флаг отзыва (если True - токен больше недействителен)
    revoked = Column(Boolean, default=False, nullable=False)
    
    # Временная метка создания
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Отношение к пользователю (один пользователь - много токенов)
    user = relationship("User", backref="tokens")
    
    def revoke(self):
        """Отзыв токена"""
        self.revoked = True
    
    @property
    def is_valid(self) -> bool:
        """Проверка, действителен ли токен"""
        return not self.revoked and self.expires_at > datetime.utcnow()
