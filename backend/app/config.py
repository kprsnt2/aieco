"""
AIEco Backend - Configuration Settings
Using Pydantic Settings for type-safe environment variables
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ----- Environment -----
    environment: str = Field(default="development", description="Current environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # ----- API -----
    api_title: str = "AIEco API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    
    # ----- Server -----
    host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    port: int = Field(default=8080, alias="BACKEND_PORT")
    
    # ----- Security -----
    jwt_secret_key: str = Field(
        default="dev-secret-change-in-production-aieco-2026",
        description="JWT signing secret (CHANGE IN PRODUCTION!)"
    )
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60 * 24 * 7  # 7 days
    api_key_header: str = "X-API-Key"
    
    # ----- Optional Services -----
    database_enabled: bool = Field(default=False, description="Enable PostgreSQL database")
    redis_enabled: bool = Field(default=False, description="Enable Redis cache")
    
    # ----- CORS -----
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )
    
    # ----- vLLM / Model Server -----
    vllm_base_url: str = Field(default="http://localhost:8000/v1", description="vLLM API URL")
    vllm_api_key: Optional[str] = Field(default=None, description="vLLM API key")
    default_model: str = Field(default="local-model", description="Default model name")
    
    # ----- Local Model Backends -----
    # Supports: "vllm", "ollama", "lmstudio", "custom"
    local_backend: str = Field(default="lmstudio", description="Local inference backend")
    ollama_base_url: str = Field(default="http://localhost:11434/v1")
    lmstudio_base_url: str = Field(default="http://localhost:1234/v1")
    local_model_name: str = Field(default="local-model")
    
    # ----- Database -----
    database_url: str = Field(
        default="postgresql+asyncpg://aieco:password@localhost:5432/aieco",
        description="PostgreSQL connection URL"
    )
    
    # ----- Redis -----
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    
    # ----- ChromaDB -----
    chroma_host: str = Field(default="localhost", description="ChromaDB host")
    chroma_port: int = Field(default=8001, description="ChromaDB port")
    
    # ----- Observability -----
    langfuse_host: Optional[str] = Field(default=None, description="Langfuse host")
    langfuse_public_key: Optional[str] = Field(default=None)
    langfuse_secret_key: Optional[str] = Field(default=None)
    
    # ----- Rate Limiting -----
    rate_limit_requests_per_minute: int = 60
    rate_limit_tokens_per_minute: int = 100000
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v
    
    @property
    def llm_base_url(self) -> str:
        """Get the appropriate LLM base URL based on backend"""
        if self.local_backend == "ollama":
            return self.ollama_base_url
        elif self.local_backend == "lmstudio":
            return self.lmstudio_base_url
        elif self.local_backend == "vllm":
            return self.vllm_base_url
        else:
            return self.vllm_base_url  # Default to vllm
    
    @property
    def llm_model(self) -> str:
        """Get the appropriate model name"""
        return self.local_model_name or self.default_model
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
