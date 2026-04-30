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

@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Создать новый элемент (только для аутентифицированных пользователей)"""
    return ItemService.create_item(db, item_data, current_user.id)

@router.get("", response_model=ItemListResponse)
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

@router.put("/{item_id}", response_model=ItemResponse)
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

@router.patch("/{item_id}", response_model=ItemResponse)
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

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
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
