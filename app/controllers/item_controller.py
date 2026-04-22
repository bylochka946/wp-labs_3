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

router = APIRouter(prefix="/items", tags=["items"])

@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    db: Session = Depends(get_db)
):
    """Создать новый элемент"""
    return ItemService.create_item(db, item_data)

@router.get("", response_model=ItemListResponse)  # ← Было dict, стало ItemListResponse
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
    item_data: ItemCreate,  # Полное обновление — все поля обязательны
    db: Session = Depends(get_db)
):
    """Полностью обновить элемент"""
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
    item_data: ItemUpdate,  # Частичное — только переданные поля
    db: Session = Depends(get_db)
):
    """Частично обновить элемент"""
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
    db: Session = Depends(get_db)
):
    """Мягкое удаление элемента"""
    success = ItemService.soft_delete_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or has been deleted"
        )
    # 204 No Content — тело ответа пустое
    return None
