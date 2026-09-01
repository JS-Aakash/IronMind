import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "IronMind Sovereign AI Workbench"
    VERSION: str = "0.1.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"

    STORAGE_UPLOADS_DIR: str = "./storage/uploads"
    STORAGE_KNOWLEDGE_DIR: str = "./storage/knowledge"
    STORAGE_ARTIFACTS_DIR: str = "./storage/artifacts"
    STORAGE_TEMP_DIR: str = "./storage/temp"

    LOCAL_INFERENCE_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    DEFAULT_REASONING_MODEL: str = "qwen2.5:7b"
    DEFAULT_VISION_MODEL: str = "qwen2.5-vl:7b"
    DEFAULT_CODER_MODEL: str = "qwen2.5-coder:7b"
    DEFAULT_EMBEDDING_MODEL: str = "bge-m3"

    STRICT_AIRGAP_ENFORCEMENT: bool = True
    ALLOW_EXTERNAL_EGRESS: bool = False

    SANDBOX_EXECUTION_MODE: str = "process"
    SANDBOX_TIMEOUT_SECONDS: int = 30

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
