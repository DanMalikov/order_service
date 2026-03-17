from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int
    postgres_username: str
    postgres_password: str
    postgres_database_name: str
    postgres_connection_string: str
    capashino_base_url: str
    api_key: str
    callback_url: str

    @computed_field(return_type=str)
    @property
    def get_db_string(self):
        url = self.postgres_connection_string
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
