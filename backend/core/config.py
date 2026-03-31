from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Papyrus"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = ""
    SYNC_DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379"

    # Auth
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1天

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()