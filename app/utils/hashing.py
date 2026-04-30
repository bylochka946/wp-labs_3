import bcrypt
import hashlib
from typing import Optional


class PasswordHasher:
    """Сервис для хеширования паролей с использованием bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хеширование пароля с автоматической генерацией соли.
        """
        # Кодируем пароль в байты
        password_bytes = password.encode('utf-8')
        
        # Генерируем соль и хешируем
        # bcrypt.gensalt() автоматически генерирует случайную соль
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Возвращаем как строку
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Проверка пароля против хеша.
        """
        try:
            # Кодируем пароль в байты
            plain_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # bcrypt.checkpw извлекает соль, хеширует и сравнивает
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
        except Exception:
            return False


class TokenHasher:
    """Сервис для хеширования токенов (для безопасного хранения в БД)"""
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Хеширование токена с использованием SHA-256.
        Используем SHA-256, так как нам не нужно проверять
        токены без знания оригинала (в отличие от паролей).
        """
        # Кодируем токен в байты
        token_bytes = token.encode('utf-8')
        
        # Создаем хеш SHA-256
        hashed = hashlib.sha256(token_bytes).hexdigest()
        
        return hashed
    
    @staticmethod
    def verify_token(plain_token: str, hashed_token: str) -> bool:
        """
        Проверка токена против хеша.
        Хэшируем предоставленный токен и сравниваем с хешем в БД.
        """
        computed_hash = TokenHasher.hash_token(plain_token)
        return computed_hash == hashed_token
