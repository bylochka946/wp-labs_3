from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID

# Базовая схема для общих полей
class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название элемента")
    description: Optional[str] = Field(None, max_length=500, description="Описание")
    status: Optional[str] = Field("active", pattern="^(active|inactive|pending)$", description="Статус")

# Для создания (все поля обязательны, кроме опциональных)
class ItemCreate(ItemBase):
    pass

# Для обновления (все поля опциональны)
class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern="^(active|inactive|pending)$")

# Для ответа (включает системные поля)
class ItemResponse(ItemBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Для пагинации (валидация параметров запроса)
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы (от 1)")
    limit: int = Field(10, ge=1, le=100, description="Количество записей на странице (1-100)")

class ItemListResponse(BaseModel):
    data: List[ItemResponse]  
    meta: dict