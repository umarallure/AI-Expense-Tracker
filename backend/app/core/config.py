"""
Core configuration settings for the AI-Powered Expense Tracker backend.
All environment variables are loaded from .env file.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    APP_NAME: str = "AI-Powered Expense Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    @field_validator('CORS_ORIGINS')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Anon/Public key
    SUPABASE_SERVICE_KEY: str  # Service role key (for admin operations)
    SUPABASE_JWT_SECRET: str
    SUPABASE_STORAGE_BUCKET: str = "documents"
    
    # Database Configuration (Direct PostgreSQL if needed)
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # OpenRouter / Cohere AI Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    COHERE_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = "cohere/command-r-plus"
    DEFAULT_EMBEDDING_MODEL: str = "cohere/embed-english-v3.0"
    
    # OpenAI Configuration (Phase 3.3)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # Cost-effective for production
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # AI Processing Settings
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.3
    EXTRACTION_CONFIDENCE_THRESHOLD: float = 0.7
    
    # n8n Workflow Configuration
    N8N_WEBHOOK_URL: Optional[str] = None
    N8N_API_KEY: Optional[str] = None
    
    # Document Processing Settings
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = "application/pdf,image/jpeg,image/png,image/tiff,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
    
    @field_validator('ALLOWED_FILE_TYPES')
    @classmethod
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [ftype.strip() for ftype in v.split(",") if ftype.strip()]
        return v
    
    # Vector Search Settings
    VECTOR_DIMENSIONS: int = 1024
    VECTOR_SEARCH_LIMIT: int = 20
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or console
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Use this function to get settings throughout the application.
    """
    return Settings()


# Global settings instance
settings = get_settings()