"""
Configuration module for the Telegram Coaching Bot.

Handles environment variables and application settings.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Application configuration."""

    telegram_bot_token: str
    admin_id: int
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        admin_id_str = os.getenv("ADMIN_ID")
        if not admin_id_str:
            raise ValueError("ADMIN_ID environment variable is required")

        try:
            admin_id = int(admin_id_str)
        except ValueError:
            raise ValueError("ADMIN_ID must be a valid integer")

        return cls(
            telegram_bot_token=token,
            admin_id=admin_id,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


# Global config instance (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
