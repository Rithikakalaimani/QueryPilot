"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "text2sql_db"
    database_type: str = "mysql"  # mysql | postgres

    # OpenAI (optional if using Ollama + HuggingFace)
    openai_api_key: str = ""

    # Embeddings: openai | huggingface (huggingface = local, no API key)
    embedding_provider: str = "huggingface"
    embedding_model: str = "all-MiniLM-L6-v2"  # HF model when provider=huggingface; OpenAI name when openai

    # LLM: openai | ollama | groq (groq = cloud, no local server)
    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"  # used when provider=groq; override for openai/ollama
    ollama_base_url: str = "http://localhost:11434"
    groq_api_key: str = ""

    # Safety
    max_rows_limit: int = 1000
    read_only: bool = True

    # Redis (optional - for sync job status, schema cache, chat cache)
    redis_host: str = ""
    redis_port: int = 17711
    redis_username: str = "default"
    redis_password: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
