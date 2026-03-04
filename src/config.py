"""配置管理"""
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # API配置
    api_title: str = "Quant Trading Agent"
    api_version: str = "0.1.0"
    
    # 数据源配置
    tushare_token: str = os.getenv("TUSHARE_TOKEN", "")
    
    # 数据库配置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    
    # LLM配置 - Moonshot Kimi
    moonshot_api_key: str = os.getenv("MOONSHOT_API_KEY", "")
    moonshot_model: str = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")
    
    class Config:
        env_file = ".env"

settings = Settings()
