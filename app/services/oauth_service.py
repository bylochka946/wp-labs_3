import httpx
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.user import User
from app.utils.jwt import JWTService
from app.utils.hashing import TokenHasher
from app.config import settings


class OAuthService:
    """Сервис для работы с OAuth провайдерами (Yandex, VK)"""
    
    # Временное хранилище state параметра (в продакшене использовать Redis)
    _state_store: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def generate_state(provider: str) -> str:
        """
        Генерация state параметра для защиты от CSRF атак.
        """
        state = secrets.token_urlsafe(32)  # Генерируем случайную строку
        
        # Сохраняем state с временем создания
        OAuthService._state_store[state] = {
            "provider": provider,
            "created_at": datetime.utcnow()
        }
        
        return state
    
    @staticmethod
    def validate_state(state: str, provider: str) -> bool:
        """
        Валидация state параметра.
        """
        if state not in OAuthService._state_store:
            return False
        
        stored_data = OAuthService._state_store[state]
        
        # Проверяем провайдера
        if stored_data["provider"] != provider:
            return False
        
        # Проверяем время (state должен быть создан не ранее 10 минут назад)
        if datetime.utcnow() - stored_data["created_at"] > timedelta(minutes=10):
            # Удаляем просроченный state
            del OAuthService._state_store[state]
            return False
        
        # State валиден, удаляем его (одноразовый)
        del OAuthService._state_store[state]
        return True
    
    @staticmethod
    async def yandex_get_auth_url() -> str:
        """
        Получение URL для авторизации через Yandex.
        """
        state = OAuthService.generate_state("yandex")
        
        params = {
            "client_id": settings.YANDEX_CLIENT_ID,
            "redirect_uri": settings.YANDEX_REDIRECT_URI,
            "response_type": "code",
            "state": state
        }
        
        # Кодируем параметры в URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{settings.YANDEX_AUTH_URL}?{query_string}"
    
    @staticmethod
    async def yandex_exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
        """
        Обмен кода авторизации на токен доступа Yandex.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.YANDEX_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.YANDEX_CLIENT_ID,
                    "client_secret": settings.YANDEX_CLIENT_SECRET,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
    
    @staticmethod
    async def yandex_get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о пользователе Yandex.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.YANDEX_USER_INFO_URL,
                headers={"Authorization": f"OAuth {access_token}"}
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
    
    @staticmethod
    async def vk_get_auth_url() -> str:
        """
        Получение URL для авторизации через VK.
        """
        state = OAuthService.generate_state("vk")
        
        params = {
            "client_id": settings.VK_CLIENT_ID,
            "redirect_uri": settings.VK_REDIRECT_URI,
            "response_type": "code",
            "state": state,
            "scope": "email"  # Запрашиваем доступ к email
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{settings.VK_AUTH_URL}?{query_string}"
    
    @staticmethod
    async def vk_exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
        """
        Обмен кода авторизации на токен доступа VK.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.VK_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.VK_CLIENT_ID,
                    "client_secret": settings.VK_CLIENT_SECRET,
                    "redirect_uri": settings.VK_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
    
    @staticmethod
    async def vk_get_user_info(access_token: str, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации о пользователе VK.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.VK_USER_INFO_URL,
                params={
                    "access_token": access_token,
                    "user_ids": user_id,
                    "v": "5.131"  # Версия API VK
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if "response" in data and len(data["response"]) > 0:
                return data["response"][0]
            
            return None
    
    @staticmethod
    def find_or_create_oauth_user(
        db: Session,
        provider: str,
        provider_id: str,
        email: str
    ) -> User:
        """
        Поиск или создание пользователя через OAuth.
        """
        # Определяем поле провайдера
        provider_field = "yandex_id" if provider == "yandex" else "vk_id"
        
        # Ищем по provider_id
        if provider == "yandex":
            user = db.query(User).filter(
                User.yandex_id == provider_id,
                User.deleted_at.is_(None)
            ).first()
        else:
            user = db.query(User).filter(
                User.vk_id == provider_id,
                User.deleted_at.is_(None)
            ).first()
        
        if user:
            return user
        
        # Ищем по email
        user = db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()
        
        if user:
            # Привязываем provider_id к существующему пользователю
            if provider == "yandex":
                user.yandex_id = provider_id
            else:
                user.vk_id = provider_id
            db.commit()
            db.refresh(user)
            return user
        
        # Создаем нового пользователя
        user = User(
            email=email,
            password_hash=None  # OAuth пользователь без пароля
        )
        
        if provider == "yandex":
            user.yandex_id = provider_id
        else:
            user.vk_id = provider_id
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def create_oauth_session(
        db: Session,
        user: User
    ) -> tuple[str, str]:
        """
        Создание сессии для OAuth пользователя.
        """
        from datetime import timedelta
        from app.models.token import Token
        
        # Генерируем токены
        access_token = JWTService.create_access_token(user.id)
        refresh_token = JWTService.create_refresh_token(user.id)
        
        # Сохраняем хеш refresh токена в БД
        refresh_token_hash = TokenHasher.hash_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_REFRESH_EXPIRATION)
        
        token_record = Token(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at
        )
        
        db.add(token_record)
        db.commit()
        
        return access_token, refresh_token
