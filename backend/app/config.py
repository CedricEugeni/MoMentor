"""Application configuration"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database/momentor.db")
    ENABLE_AUTO_SCHEDULING: bool = os.getenv("ENABLE_AUTO_SCHEDULING", "true").lower() == "true"
    TIMEZONE: str = os.getenv("TZ", "Europe/Paris")
    
    class Config:
        env_file = ".env"


settings = Settings()
