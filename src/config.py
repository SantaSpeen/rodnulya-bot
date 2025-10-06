"""Configuration management for the bot."""
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Bot settings
    bot_token: str = Field(..., description="Telegram bot token")
    
    # Database settings
    database_type: Literal["sqlite", "postgresql"] = Field(
        default="sqlite",
        description="Database type to use"
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./bot.db",
        description="Database connection URL"
    )
    
    # HTTP server settings
    http_host: str = Field(default="0.0.0.0", description="HTTP server host")
    http_port: int = Field(default=8080, description="HTTP server port")
    webhook_secret: str = Field(
        default="change_me_in_production",
        description="Secret for validating webhooks"
    )


settings = Settings()
