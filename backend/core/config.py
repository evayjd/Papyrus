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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # Arxiv MCP
    ARXIV_API_URL: str = "https://export.arxiv.org/api/query"
    ARXIV_MAX_RESULTS: int = 5
    ARXIV_TIMEOUT: int = 30

    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Ollama
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    #others
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()