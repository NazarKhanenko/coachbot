"""
Telegram Coaching Bot - A private coaching platform.

Architecture:
- handlers/: Message and callback handlers
- services/: Business logic layer
- storage/: Data persistence (in-memory for now)
- keyboards/: Inline and reply keyboard builders
- models/: Domain models (not DB models yet)
- docs/: Documentation
- media/: Static media files
"""

import logging

from config import get_config

from handlers import setup_handlers


def create_bot() -> None:
    """Initialize and run the bot."""
    config = get_config()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Telegram Coaching Bot...")

    # TODO: Initialize Aiogram bot and dispatcher here
    # from aiogram import Bot, Dispatcher
    # bot = Bot(token=config.telegram_bot_token)
    # dp = Dispatcher()

    # Setup handlers
    # setup_handlers(dp)

    # TODO: Start polling
    # await dp.start_polling(bot)

    logger.info("Bot architecture initialized successfully.")


if __name__ == "__main__":
    create_bot()
