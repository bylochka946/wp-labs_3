from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.item import (
    ItemCreate, ItemUpdate, ItemResponse, 
    PaginationParams, ItemListResponse
)
from app.services.item_service import ItemService
from app.utils.pagination import get_paginated_response
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/items", tags=["items"])

@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый элемент",
    description="Создает новый элемент. Требует аутентификации. Элемент автоматически привязывается к текущему пользователю.",
    responses={
        201: {
            "description": "Элемент успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Новый элемент",
                        "description": "Описание элемента",
                        "status": "active",
                        "owner_id": "456e7890-e12b-34d5-a678-901234567890",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00",
                        "deleted_at": None
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request data"}
                }
            }
        },
        401: {
            "description": "Пользователь не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            }
        }
    }
)
def create_item(
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Создать новый элемент (только для аутентифицированных пользователей)"""
    return ItemService.create_item(db, item_data, current_user.id)

@router.get(
    "",
    response_model=ItemListResponse,
    summary="Получить список элементов",
    description="Возвращает список активных элементов с пагинацией. Не требует аутентификации.",
    responses={
        200: {
            "description": "Список элементов с метаданными пагинации",
            "content": {
                "application/json": {
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
            }
        }
    }
)
def get_items(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """Получить список активных элементов с пагинацией"""
    items, total = ItemService.get_items_paginated(db, pagination)
    
    return get_paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit
    )

@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Полное обновление элемента",
    description="Полностью обновляет элемент (заменяет все поля). Требует аутентификации и владения элементом.",
    responses={
        200: {
            "description": "Элемент успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Обновленный элемент",
                        "description": "Новое описание",
                        "status": "inactive",
                        "owner_id": "456e7890-e12b-34d5-a678-901234567890",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T11:00:00",
                        "deleted_at": None
                    }
                }
            }
        },
        401: {
            "description": "Пользователь не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            }
        },
        403: {
            "description": "Пользователь не является владельцем элемента",
            "content": {
                "application/json": {
                    "example": {"detail": "You don't have permission to update this item"}
                }
            }
        },
        404: {
            "description": "Элемент не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found or has been deleted"}
                }
            }
        }
    }
)
def update_item_full(
    item_id: str,
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Полностью обновить элемент (только владелец)"""
    # Проверяем владение
    if not ItemService.check_ownership(db, item_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this item"
        )
    
    updated = ItemService.update_item(db, item_id, item_data, full_update=True)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or has been deleted"
        )
    return updated

@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Частичное обновление элемента",
    description="Частично обновляет элемент (только указанные поля). Требует аутентификации и владения элементом.",
    responses={
        200: {
            "description": "Элемент успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Обновленный элемент",
                        "description": "Обновленное описание",
                        "status": "pending",
                        "owner_id": "456e7890-e12b-34d5-a678-901234567890",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T11:00:00",
                        "deleted_at": None
                    }
                }
            }
        },
        401: {
            "description": "Пользователь не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            }
        },
        403: {
            "description": "Пользователь не является владельцем элемента",
            "content": {
                "application/json": {
                    "example": {"detail": "You don't have permission to update this item"}
                }
            }
        },
        404: {
            "description": "Элемент не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found or has been deleted"}
                }
            }
        }
    }
)
def update_item_partial(
    item_id: str,
    item_data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Частично обновить элемент (только владелец)"""
    # Проверяем владение
    if not ItemService.check_ownership(db, item_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this item"
        )
    
    updated = ItemService.update_item(db, item_id, item_data, full_update=False)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or has been deleted"
        )
    return updated

@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить элемент (soft delete)",
    description="Мягко удаляет элемент (устанавливает deleted_at). Требует аутентификации и владения элементом.",
    responses={
        204: {
            "description": "Элемент успешно удален"
        },
        401: {
            "description": "Пользователь не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            }
        },
        403: {
            "description": "Пользователь не является владельцем элемента",
            "content": {
                "application/json": {
                    "example": {"detail": "You don't have permission to delete this item"}
                }
            }
        },
        404: {
            "description": "Элемент не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Item not found or has been deleted"}
                }
            }
        }
    }
)
def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Мягкое удаление элемента (только владелец)"""
    # Проверяем владение
    if not ItemService.check_ownership(db, item_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this item"
        )
    
    success = ItemService.soft_delete_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or has been deleted"
        )
    # 204 No Content — тело ответа пустое
    return None
