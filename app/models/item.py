from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.database import Base

class Item(Base):
    __tablename__ = "items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="active")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Поле для мягкого удаления (Soft Delete)
    deleted_at = Column(DateTime, nullable=True)
    
    def mark_as_deleted(self):
        """Метод для мягкого удаления"""
        self.deleted_at = datetime.utcnow()
    
    @property
    def is_deleted(self) -> bool:
        """Проверка, удалён ли элемент"""
        return self.deleted_at is not None