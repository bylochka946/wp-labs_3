from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
import re


class UserRegister(BaseModel):
    """Схема для регистрации нового пользователя"""
    email: EmailStr = Field(
        ...,
        description="Email адрес пользователя (уникальный)",
        json_schema_extra={"examples": ["user@example.com"]}
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Пароль (минимум 8 символов, 1 заглавная, 1 строчная, 1 цифра)",
        json_schema_extra={"examples": ["SecurePass123"]}
    )
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Валидация сложности пароля"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class UserLogin(BaseModel):
    """Схема для входа пользователя"""
    email: EmailStr = Field(
        ...,
        description="Email адрес пользователя",
        json_schema_extra={"examples": ["user@example.com"]}
    )
    password: str = Field(
        ...,
        description="Пароль пользователя",
        json_schema_extra={"examples": ["SecurePass123"]}
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя (БЕЗ чувствительных данных)"""
    id: UUID = Field(
        ...,
        description="Уникальный идентификатор пользователя (UUID)"
    )
    email: str = Field(
        ...,
        description="Email адрес пользователя"
    )
    created_at: datetime = Field(
        ...,
        description="Дата и время создания аккаунта"
    )
    updated_at: datetime = Field(
        ...,
        description="Дата и время последнего обновления"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class PasswordChange(BaseModel):
    """Схема для смены пароля"""
    old_password: str = Field(
        ...,
        description="Текущий пароль пользователя"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="Новый пароль (минимум 8 символов, 1 заглавная, 1 строчная, 1 цифра)"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """Валидация сложности нового пароля"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "OldPass123",
                "new_password": "NewPass456"
            }
        }


class PasswordResetRequest(BaseModel):
    """Схема для запроса на сброс пароля"""
    email: EmailStr = Field(
        ...,
        description="Email адрес пользователя для отправки токена сброса пароля",
        json_schema_extra={"examples": ["user@example.com"]}
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordReset(BaseModel):
    """Схема для установки нового пароля"""
    token: str = Field(
        ...,
        description="Токен сброса пароля (полученный по email)",
        json_schema_extra={"examples": ["AbC123XyZ_TokenHere"]}
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="Новый пароль (минимум 8 символов, 1 заглавная, 1 строчная, 1 цифра)",
        json_schema_extra={"examples": ["NewSecurePass789"]}
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """Валидация сложности нового пароля"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "AbC123XyZ_TokenHere",
                "new_password": "NewSecurePass789"
            }
        }


class TokenResponse(BaseModel):
    """Схема для ответа с токеном"""
    access_token: str = Field(
        ...,
        description="JWT Access Token (передается в HttpOnly cookie)"
    )
    refresh_token: str = Field(
        ...,
        description="JWT Refresh Token (передается в HttpOnly cookie)"
    )
    token_type: str = Field(
        "bearer",
        description="Тип токена"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class OAuthState(BaseModel):
    """Схема для хранения state параметра (защита от CSRF)"""
    state: str = Field(
        ...,
        description="Уникальный state параметр для защиты от CSRF атак"
    )
    provider: str = Field(
        ...,
        description="Название OAuth провайдера (yandex или vk)"
    )
    created_at: datetime = Field(
        ...,
        description="Время создания state параметра"
    )
