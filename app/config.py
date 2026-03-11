from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int
    postgres_username: str
    postgres_password: str
    postgres_database_name: str
    postgres_connection_string: str | None = None
    capashino_base_url: str
    api_key: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_url(self) -> str:
        """Метод для изменения строки соединения postgresql"""
        if self.postgres_connection_string:
            return self.postgres_connection_string
        return (
            f"postgresql+asyncpg://{self.postgres_username}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database_name}"
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
print("database_url =", settings.postgres_connection_string)
print("sqlalchemy_database_url =", settings.sqlalchemy_database_url)
