from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re


class UserRegister(BaseModel):
    """Схема для регистрации нового пользователя"""
    email: EmailStr
    password: str
    
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


class UserLogin(BaseModel):
    """Схема для входа пользователя"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя (БЕЗ чувствительных данных)"""
    id: UUID
    email: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Схема для смены пароля"""
    old_password: str
    new_password: str
    
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


class PasswordResetRequest(BaseModel):
    """Схема для запроса на сброс пароля"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Схема для установки нового пароля"""
    token: str
    new_password: str
    
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


class TokenResponse(BaseModel):
    """Схема для ответа с токеном"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OAuthState(BaseModel):
    """Схема для хранения state параметра (защита от CSRF)"""
    state: str
    provider: str
    created_at: datetime
