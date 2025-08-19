from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Skeleton"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRES_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRES_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    RATE_LIMIT_DEFAULT_LIMIT: int = 60
    RATE_LIMIT_DEFAULT_WINDOW: int = 60
    RATE_LIMIT_LOGIN_LIMIT: int = 5
    RATE_LIMIT_LOGIN_WINDOW: int = 60
    ENVIRONMENT: str = "dev"
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
