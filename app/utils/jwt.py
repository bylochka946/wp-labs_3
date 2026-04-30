import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from app.config import settings


class JWTService:
    """Сервис для работы с JWT токенами"""
    
    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        """
        Создание Access токена.
        
        Access токен:
        - Короткое время жизни (15 минут)
        - Используется для доступа к защищенным ресурсам
        - Передается в cookies с флагом HttpOnly
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=settings.JWT_ACCESS_EXPIRATION)
        
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": expire,
            "iat": now
        }
        
        # Подписываем токен секретным ключом
        token = jwt.encode(
            payload,
            settings.JWT_ACCESS_SECRET,
            algorithm="HS256"
        )
        
        return token
    
    @staticmethod
    def create_refresh_token(user_id: UUID) -> str:
        """
        Создание Refresh токена.
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=settings.JWT_REFRESH_EXPIRATION)
        
        # Генерируем уникальный идентификатор для токена
        import uuid
        jti = str(uuid.uuid4())
        
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": now,
            "jti": jti
        }
        
        # Подписываем токен другим секретным ключом
        token = jwt.encode(
            payload,
            settings.JWT_REFRESH_SECRET,
            algorithm="HS256"
        )
        
        return token
    
    @staticmethod
    def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Проверка и декодирование Access токена.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_ACCESS_SECRET,
                algorithms=["HS256"]
            )
            
            # Проверяем, что это именно access токен
            if payload.get("type") != "access":
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            # Токен просрочен
            return None
        except jwt.InvalidTokenError:
            # Неверная подпись или формат
            return None
    
    @staticmethod
    def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Проверка и декодирование Refresh токена.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_REFRESH_SECRET,
                algorithms=["HS256"]
            )
            
            # Проверяем, что это именно refresh токен
            if payload.get("type") != "refresh":
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            # Токен просрочен
            return None
        except jwt.InvalidTokenError:
            # Неверная подпись или формат
            return None
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[str]:
        """
        Извлечение идентификатора пользователя из токена.
        Сначала пытаемся как access токен, потом как refresh.
        """
        # Пробуем как access токен
        payload = JWTService.verify_access_token(token)
        if payload:
            return payload.get("sub")
        
        # Пробуем как refresh токен
        payload = JWTService.verify_refresh_token(token)
        if payload:
            return payload.get("sub")
        
        return None
