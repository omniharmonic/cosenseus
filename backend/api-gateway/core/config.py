"""
Configuration management for the API Gateway service
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Civic Sense-Making Platform API Gateway"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://localhost:3000",
        "https://localhost:3001"
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/census"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Microservices URLs
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    EVENT_SERVICE_URL: str = "http://event-service:8002"
    NLP_SERVICE_URL: str = "http://nlp_service:8003"
    PROFILE_SERVICE_URL: str = "http://profile-service:8004"
    
    # External Services
    SPEECH_TO_TEXT_SERVICE: str = "openai"  # or "azure", "google"
    OPENAI_API_KEY: Optional[str] = None
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Monitoring
    PROMETHEUS_METRICS: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Vector Database
    VECTOR_DB_TYPE: str = "chroma"  # or "pinecone", "weaviate"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # Email Service
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "/tmp/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings() 