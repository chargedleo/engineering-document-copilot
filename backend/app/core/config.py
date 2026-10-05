from pathlib import Path
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Information
    APP_NAME: str = "Engineering Document Intelligence & CAD Knowledge Copilot"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    API_V1_PREFIX: str = "/api/v1"

    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # Database Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "engineering_copilot"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/engineering_copilot"

    # Azure OpenAI Configuration (Optional for Milestone 2 - Staging / Configuration only)
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = "gpt-4o"
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: Optional[str] = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: Optional[str] = "text-embedding-3-large"

    # Azure AI Search Configuration (Optional for Milestone 2 - Staging / Configuration only)
    AZURE_SEARCH_ENDPOINT: Optional[str] = None
    AZURE_SEARCH_API_KEY: Optional[str] = None
    AZURE_SEARCH_INDEX_NAME: Optional[str] = "engineering-docs-index"
    AZURE_SEARCH_DOCUMENTS_INDEX_NAME: Optional[str] = "engineering-docs-index"
    AZURE_SEARCH_CAD_INDEX_NAME: Optional[str] = "cad-knowledge-index"

    # Storage Paths (Resolved relative to project root)
    DOCUMENTS_STORAGE_DIR: str = str(
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents"
    )
    PROCESSED_STORAGE_DIR: str = str(
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed"
    )

    # Document Intelligence & OCR Configuration (Milestone 3)
    TESSERACT_CMD: Optional[str] = None
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_PDF_PAGES: int = 500
    PDF_MIN_NATIVE_TEXT_CHARS: int = 50
    OCR_DPI: int = 300

    # Document Chunking & Hybrid Search Configuration (Milestone 4)
    CHUNK_SIZE_CHARS: int = 800
    CHUNK_OVERLAP_CHARS: int = 150
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_PROVIDER: str = "auto"  # "auto", "azure", "local"
    SEARCH_PROVIDER: str = "auto"     # "auto", "azure", "local"
    HYBRID_SEARCH_TOP_K: int = 5

    # Retrieval-Augmented Generation (RAG) Configuration (Milestone 5)
    LLM_PROVIDER: str = "auto"  # "auto", "azure", "local"
    AZURE_OPENAI_CHAT_DEPLOYMENT: Optional[str] = "gpt-4o"
    RAG_RELEVANCE_THRESHOLD: float = 0.01
    RAG_DEFAULT_TOP_K: int = 5


settings = Settings()
