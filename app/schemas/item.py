from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID

# Базовая схема для общих полей
class ItemBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Название элемента",
        json_schema_extra={"examples": ["Мой новый элемент"]}
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Описание элемента (опционально)",
        json_schema_extra={"examples": ["Это подробное описание моего элемента"]}
    )
    status: Optional[str] = Field(
        "active",
        pattern="^(active|inactive|pending)$",
        description="Статус элемента: active (активный), inactive (неактивный), pending (ожидание)"
    )

# Для создания (все поля обязательны, кроме опциональных)
class ItemCreate(ItemBase):
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Новый элемент",
                "description": "Описание элемента",
                "status": "active"
            }
        }

# Для обновления (все поля опциональны)
class ItemUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Новое название элемента"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Новое описание элемента"
    )
    status: Optional[str] = Field(
        None,
        pattern="^(active|inactive|pending)$",
        description="Новый статус элемента"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Обновленный элемент",
                "description": "Обновленное описание",
                "status": "inactive"
            }
        }

# Для ответа (включает системные поля)
class ItemResponse(ItemBase):
    id: UUID = Field(
        ...,
        description="Уникальный идентификатор элемента (UUID)"
    )
    owner_id: UUID = Field(
        ...,
        description="Идентификатор владельца элемента (UUID)"
    )
    created_at: datetime = Field(
        ...,
        description="Дата и время создания элемента"
    )
    updated_at: datetime = Field(
        ...,
        description="Дата и время последнего обновления"
    )
    deleted_at: Optional[datetime] = Field(
        None,
        description="Дата и время удаления (None если не удален)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Мой элемент",
                "description": "Описание элемента",
                "status": "active",
                "owner_id": "456e7890-e12b-34d5-a678-901234567890",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00",
                "deleted_at": None
            }
        }
    )

# Для пагинации (валидация параметров запроса)
class PaginationParams(BaseModel):
    page: int = Field(
        1,
        ge=1,
        description="Номер страницы (начиная с 1)",
        json_schema_extra={"examples": [1]}
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Количество записей на странице (от 1 до 100)",
        json_schema_extra={"examples": [10]}
    )

class ItemListResponse(BaseModel):
    data: List[ItemResponse] = Field(
        ...,
        description="Список элементов"
    )
    meta: dict = Field(
        ...,
        description="Метаданные пагинации",
        json_schema_extra={
            "example": {
                "page": 1,
                "limit": 10,
                "total": 100,
                "pages": 10
            }
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Элемент 1",
                        "description": "Описание",
                        "status": "active",
                        "owner_id": "456e7890-e12b-34d5-a678-901234567890",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00",
                        "deleted_at": None
                    }
                ],
                "meta": {
                    "page": 1,
                    "limit": 10,
                    "total": 1,
                    "pages": 1
                }
            }
        }