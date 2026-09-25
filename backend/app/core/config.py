from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.6-flash"
    DOCUMENT_CHUNK_SIZE: int = 1000
    DOCUMENT_CHUNK_OVERLAP: int = 200
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    
    # RAG Settings
    RAG_SIMILARITY_THRESHOLD: float = 0.5
    RAG_MAX_CONTEXT_CHARACTERS: int = 15000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
