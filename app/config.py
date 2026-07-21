import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    app_name: str = "CommerceFlow API"
    environment: str = "dev"
    api_base: str = "http://localhost:8080"
    
    # Database Settings
    # Use in-memory SQLite by default for easy test/run, or asyncpg for Postgres
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/commerceflow"
    
    # Redis & Celery Settings
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # JWT Security Settings
    jwt_secret: str = "supersecretsecuritykeyforcommerceflowapi123!"
    jwt_algorithm: str = "HS256"
    jwt_access_expiration_minutes: int = 15
    jwt_refresh_expiration_days: int = 7
    
    # Brute Force Mitigation Settings
    failed_login_attempts_limit: int = 5
    account_lock_minutes: int = 30
    
    # Verification Settings
    email_verification_expiry_hours: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
