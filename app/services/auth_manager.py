from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from app.models.user import User
from app.models.token import Token
from app.schemas.auth import UserRegister, UserLogin
from app.utils.hashing import PasswordHasher, TokenHasher
from app.utils.jwt import JWTService
from app.config import settings


class AuthManager:
    """Менеджер аутентификации - бизнес-логика"""
    
    @staticmethod
    def register_user(db: Session, register_data: UserRegister) -> User:
        """
        Регистрация нового пользователя.
        """
        # Проверяем, нет ли уже пользователя с таким email
        existing_user = db.execute(
            select(User).where(
                User.email == register_data.email,
                User.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
        
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Хешируем пароль (bcrypt автоматически генерирует соль)
        password_hash = PasswordHasher.hash_password(register_data.password)
        
        # Создаем пользователя
        user = User(
            email=register_data.email,
            password_hash=password_hash
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def register_and_login(
        db: Session, 
        register_data: UserRegister
    ) -> Tuple[User, str, str]:
        """
        Регистрация с автоматическим входом.
        """
        # Регистрируем пользователя
        user = AuthManager.register_user(db, register_data)
        
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
        
        return user, access_token, refresh_token
    
    @staticmethod
    def login_user(
        db: Session, 
        login_data: UserLogin
    ) -> Tuple[User, str, str]:
        """
        Вход пользователя (логин).
        """
        # Находим пользователя по email
        user = db.execute(
            select(User).where(
                User.email == login_data.email,
                User.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Проверяем, есть ли у пользователя пароль (не OAuth пользователь)
        if not user.password_hash:
            raise ValueError("Invalid email or password")
        
        # Проверяем пароль
        if not PasswordHasher.verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # Генерируем токены
        access_token = JWTService.create_access_token(user.id)
        refresh_token = JWTService.create_refresh_token(user.id)
        
        # Сохраняем хеш refresh токена в БД (для возможности отзыва)
        refresh_token_hash = TokenHasher.hash_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_REFRESH_EXPIRATION)
        
        token_record = Token(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at
        )
        
        db.add(token_record)
        db.commit()
        
        return user, access_token, refresh_token
    
    @staticmethod
    def refresh_tokens(
        db: Session, 
        refresh_token: str
    ) -> Tuple[str, str]:
        """
        Обновление пары токенов.
        """
        # Проверяем валидность токена (подпись, срок)
        payload = JWTService.verify_refresh_token(refresh_token)
        if payload is None:
            raise ValueError("Invalid or expired refresh token")
        
        # Извлекаем ID пользователя
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Хешируем предоставленный токен для поиска в БД
        token_hash = TokenHasher.hash_token(refresh_token)
        
        # Находим токен в БД
        token_record = db.execute(
            select(Token).where(
                Token.token_hash == token_hash,
                Token.user_id == UUID(user_id)
            )
        ).scalar_one_or_none()
        
        if not token_record:
            raise ValueError("Token not found in database")
        
        # Проверяем, что токен не отозван
        if token_record.revoked:
            raise ValueError("Token has been revoked")
        
        # Проверяем срок действия
        if token_record.expires_at < datetime.utcnow():
            raise ValueError("Token has expired")
        
        # Генерируем новую пару токенов
        new_access_token = JWTService.create_access_token(UUID(user_id))
        new_refresh_token = JWTService.create_refresh_token(UUID(user_id))
        
        # Отзываем старый токен
        token_record.revoke()
        
        # Сохраняем новый refresh токен
        new_token_hash = TokenHasher.hash_token(new_refresh_token)
        new_expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_REFRESH_EXPIRATION)
        
        new_token_record = Token(
            user_id=UUID(user_id),
            token_hash=new_token_hash,
            expires_at=new_expires_at
        )
        
        db.add(new_token_record)
        db.commit()
        
        return new_access_token, new_refresh_token
    
    @staticmethod
    def logout_user(db: Session, refresh_token: str) -> bool:
        """
        Завершение текущей сессии (отзыв токена).
        """
        token_hash = TokenHasher.hash_token(refresh_token)
        
        token_record = db.execute(
            select(Token).where(Token.token_hash == token_hash)
        ).scalar_one_or_none()
        
        if token_record:
            token_record.revoke()
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def logout_all_user_sessions(db: Session, user_id: UUID) -> int:
        """
        Завершение всех сессий пользователя.
        """
        tokens = db.execute(
            select(Token).where(
                Token.user_id == user_id,
                Token.revoked == False
            )
        ).scalars().all()
        
        count = 0
        for token in tokens:
            token.revoke()
            count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Получение пользователя по ID"""
        return db.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        return db.execute(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
