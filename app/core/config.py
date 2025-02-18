from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    TOKEN: str = Field(..., min_length=1)

    DB_HOST: str = Field(...)
    DB_PORT: int = Field(...)
    DB_NAME: str = Field(...)
    DB_USER: str = Field(...)
    DB_PASSWORD: str = Field(...)

    VPN_TYPE: str = Field(default="H")

    # Новый список админов (здесь укажите свои telegram_id)
    ADMIN_IDS: list[int] = Field(default_factory=lambda: [683286025])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()