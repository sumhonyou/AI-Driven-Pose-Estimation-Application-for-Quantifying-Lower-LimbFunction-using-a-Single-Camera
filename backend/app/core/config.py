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
    cors_origins: str = "http://localhost:5173,http://localhost:5180"
    # Optional after-set feedback rewrite. Reports work fully with this disabled.
    llm_api_key: str | None = None
    llm_model: str = "llama-3.3-70b-versatile"
    feedback_llm_enabled: bool = False
    # Root log level (see core/logging_config.py). INFO keeps the diagnostics that
    # explain a template fallback visible by default; set LOG_LEVEL=DEBUG in .env for a
    # noisier session, or WARNING to quieten it.
    log_level: str = "INFO"


settings = Settings()
