from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime
from typing import List, Tuple, Optional

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate, PaginationParams

class ItemService:
    
    @staticmethod
    def create_item(db: Session, item_data: ItemCreate) -> Item:
        """Создание нового элемента"""
        db_item = Item(**item_data.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def get_item_by_id(db: Session, item_id: str) -> Optional[Item]:
        """Получение элемента по ID (исключая удалённые)"""
        return db.execute(
            select(Item).where(
                Item.id == item_id,
                Item.deleted_at.is_(None)  # Исключаем удалённые
            )
        ).scalar_one_or_none()
    
    @staticmethod
    def get_items_paginated(
        db: Session, 
        pagination: PaginationParams
    ) -> Tuple[List[Item], int]:
        """
        Получение списка с пагинацией.
        Возвращает: (список элементов, общее количество НЕудалённых)
        """
        offset = (pagination.page - 1) * pagination.limit
        
        # Запрос с фильтрацией удалённых
        query = select(Item).where(Item.deleted_at.is_(None))
        
        # Получаем общее количество для мета-информации
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        
        # Добавляем пагинацию и выполняем
        items = db.execute(
            query.offset(offset).limit(pagination.limit)
        ).scalars().all()
        
        return items, total
    
    @staticmethod
    def update_item(
        db: Session, 
        item_id: str, 
        item_data: ItemUpdate,
        full_update: bool = False
    ) -> Optional[Item]:
        """Обновление элемента (полное или частичное)"""
        db_item = ItemService.get_item_by_id(db, item_id)
        if not db_item:
            return None
        
        # Получаем данные для обновления
        update_data = item_data.model_dump(exclude_unset=True)
        if full_update:
            # Для PUT: если поле не передано, устанавливаем None (кроме id)
            for field in ['name', 'description', 'status']:
                if field not in update_data:
                    update_data[field] = None
        
        # Обновляем только переданные поля
        for field, value in update_data.items():
            if hasattr(db_item, field):
                setattr(db_item, field, value)
        
        db_item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def soft_delete_item(db: Session, item_id: str) -> bool:
        """Мягкое удаление: помечаем запись как удалённую"""
        db_item = ItemService.get_item_by_id(db, item_id)
        if not db_item:
            return False
        
        db_item.mark_as_deleted()
        db.commit()
        return True