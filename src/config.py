"""配置管理"""
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    tushare_token: str = os.getenv("TUSHARE_TOKEN", "")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    
    class Config:
        env_file = ".env"

settings = Settings()
