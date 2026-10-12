"""TripMind Configuration & Settings.

Loads environment variables with Pydantic Settings.
Allows dynamic toggling between real LLM providers (Gemini, Groq)
and a deterministic offline mock provider for automated unit testing.
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Provider selection: 'gemini', 'groq', or 'mock'
    TRIPMIND_LLM_PROVIDER: Literal["gemini", "groq", "mock"] = "gemini"

    # Database Configuration (Dedicated PostgreSQL on port 5433)
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5433/tripmind"

    # API Keys
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Models
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # Agent Loop Safeguards
    # Guardrail: Never let an autonomous agent loop infinitely.
    # Max iterations bounds both token consumption and execution latency.
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 60

    # API Server Config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False


settings = Settings()
