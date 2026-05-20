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

import asyncio
import logging

from aiogram import Bot, Dispatcher

from .config import config
from .handlers import setup_handlers
from .services.athlete_service import AthleteService
from .storage.athlete_storage import AthleteStorage


async def create_bot() -> None:
    """Initialize and run the bot."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Telegram Coaching Bot...")

    # Initialize Aiogram bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Initialize services (singletons for now)
    athlete_storage = AthleteStorage()
    athlete_service = AthleteService(storage=athlete_storage)

    # Setup handlers with services
    setup_handlers(dp, athlete_service)

    logger.info("Bot initialized successfully. Starting polling...")

    try:
        # Start polling
        await dp.start_polling(bot)
    finally:
        # Cleanup
        await bot.session.close()
        logger.info("Bot stopped.")


def main() -> None:
    """Entry point for the bot."""
    asyncio.run(create_bot())


if __name__ == "__main__":
    main()
