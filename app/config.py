"""Application configuration management using Pydantic Settings."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "AI-Powered Website Link Analysis API"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 4000
    DEBUG: bool = False

    # LLM Settings
    # Supported providers: "gemini", "openai", "mock"
    LLM_PROVIDER: str = Field(default="gemini", description="LLM provider: gemini, openai, or mock")
    
    # Google Gemini Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="API Key for Google Gemini")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Google Gemini model identifier")
    
    # OpenAI Configuration (also supports OpenAI-compatible endpoints like Groq, Ollama, OpenRouter)
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="API Key for OpenAI")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI model identifier")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, description="Custom base URL for OpenAI-compatible APIs")

    # Scraper & Extraction Settings
    SCRAPER_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 DxoraLinkAnalysis/1.0"
    )
    REQUEST_TIMEOUT: int = Field(default=15, description="Timeout in seconds for external HTTP requests")
    MAX_CONTENT_LENGTH: int = Field(
        default=25000,
        description="Maximum characters of website extracted content to pass to LLM (Token Cost Optimization)"
    )

    # Caching Settings
    ENABLE_CACHE: bool = Field(default=True, description="Enable in-memory response caching")
    CACHE_TTL_SECONDS: int = Field(default=3600, description="Cache TTL in seconds")


settings = Settings()
