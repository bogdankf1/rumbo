from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    database_url: str = "postgresql+asyncpg://rumbo:rumbo@localhost:5433/rumbo"
    claude_model: str = "claude-opus-5"
    embedding_model: str = "text-embedding-3-small"
    embedding_dims: int = 1536


settings = Settings()
