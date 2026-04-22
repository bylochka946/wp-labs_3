# app/config.py (исправленная версия)
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_USER: str = os.getenv("DB_USER", "student")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "student_secure_password")
    DB_NAME: str = os.getenv("DB_NAME", "wp_labs")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()