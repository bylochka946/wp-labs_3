# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Application Environment
    APP_ENV: str = os.getenv("APP_ENV", "development")
    
    # Database Configuration
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # JWT Configuration
    JWT_ACCESS_SECRET: str = os.getenv("JWT_ACCESS_SECRET", "access_secret_key")
    JWT_REFRESH_SECRET: str = os.getenv("JWT_REFRESH_SECRET", "refresh_secret_key")
    JWT_ACCESS_EXPIRATION: int = int(os.getenv("JWT_ACCESS_EXPIRATION", "15"))  # minutes
    JWT_REFRESH_EXPIRATION: int = int(os.getenv("JWT_REFRESH_EXPIRATION", "10080"))  # minutes (7 days)
    
    # OAuth Yandex Configuration
    YANDEX_CLIENT_ID: str = os.getenv("YANDEX_CLIENT_ID", "")
    YANDEX_CLIENT_SECRET: str = os.getenv("YANDEX_CLIENT_SECRET", "")
    YANDEX_REDIRECT_URI: str = os.getenv("YANDEX_REDIRECT_URI", "http://localhost:8000/auth/oauth/yandex/callback")
    
    # OAuth VK Configuration
    VK_CLIENT_ID: str = os.getenv("VK_CLIENT_ID", "")
    VK_CLIENT_SECRET: str = os.getenv("VK_CLIENT_SECRET", "")
    VK_REDIRECT_URI: str = os.getenv("VK_REDIRECT_URI", "http://localhost:8000/auth/oauth/vk/callback")
    
    # OAuth Provider URLs
    YANDEX_AUTH_URL: str = "https://oauth.yandex.ru/authorize"
    YANDEX_TOKEN_URL: str = "https://oauth.yandex.ru/token"
    YANDEX_USER_INFO_URL: str = "https://login.yandex.ru/info"
    
    VK_AUTH_URL: str = "https://oauth.vk.com/authorize"
    VK_TOKEN_URL: str = "https://oauth.vk.com/access_token"
    VK_USER_INFO_URL: str = "https://api.vk.com/method/users.get"

settings = Settings()