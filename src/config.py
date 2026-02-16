from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Auth
    AUTH_PROVIDER: str = "env"
    API_KEYS: str = ""
    RATE_LIMIT: str = "60/minute"

    # LLM Provider
    LLM_PROVIDER: str = "openrouter"

    # OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Default models
    DEFAULT_BASE_MODEL_OCR: str = "google/gemini-flash-1.5"
    DEFAULT_ADVANCED_MODEL_OCR: str = "google/gemini-pro-vision"
    DEFAULT_BASE_MODEL_PARSE: str = "google/gemini-flash-1.5"
    DEFAULT_ADVANCED_MODEL_PARSE: str = "openai/gpt-4o-mini"

    # Limits
    MAX_FILE_SIZE_MB: int = 10
    REQUEST_TIMEOUT_SECONDS: int = 60
    LOG_LEVEL: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def api_keys_list(self) -> list[str]:
        if not self.API_KEYS:
            return []
        return [k.strip() for k in self.API_KEYS.split(",") if k.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()
