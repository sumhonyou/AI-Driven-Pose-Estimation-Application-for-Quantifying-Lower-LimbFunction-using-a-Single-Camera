from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://fyp_user:fyp_password@localhost:5432/fyp_rehab_db"
    )
    jwt_secret_key: str = "change_this_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    llm_api_key: str | None = None
    llm_api_base_url: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:5180"


settings = Settings()
