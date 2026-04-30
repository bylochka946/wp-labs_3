from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.utils.jwt import JWTService


class AuthService:
    """Сервис для аутентификации и авторизации"""
    
    @staticmethod
    def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
    ) -> User:
        """
        Получение текущего аутентифицированного пользователя.
        """
        # Извлекаем токен из cookies
        access_token = request.cookies.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Cookie"},
            )
        
        # Проверяем валидность токена
        payload = JWTService.verify_access_token(access_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Cookie"},
            )
        
        # Извлекаем ID пользователя
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Cookie"},
            )
        
        # Находим пользователя в БД
        user = db.query(User).filter(
            User.id == UUID(user_id),
            User.deleted_at.is_(None)  # Исключаем удаленных пользователей
        ).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Cookie"},
            )
        
        return user
    
    @staticmethod
    def get_current_user_optional(
        request: Request,
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """
        Получение текущего пользователя.
        """
        try:
            return AuthService.get_current_user(request, db)
        except HTTPException:
            return None
