"""Nexus configuration"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "Nexus_3"
    version: str = "0.1.0"
    debug: bool = True
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8100
    
    # Cortex integration
    cortex_api_url: str = "http://localhost:8000"
    cortex_timeout: int = 30
    
    # Service settings
    max_concurrent_tasks: int = 10
    task_timeout: int = 300  # 5 minutes
    
    class Config:
        env_prefix = "NEXUS_"

settings = Settings()
