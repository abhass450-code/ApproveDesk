from functools import lru_cache
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ApproveDesk API"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://approvedesk:local_dev_password_change_me@localhost:5432/approvedesk"
    jwt_secret: SecretStr = SecretStr("dev-only-change-this-secret-before-any-deployment-123456")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:3000"]
    upload_dir: Path = Path("uploads")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
