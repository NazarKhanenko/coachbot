"""
Message handlers for the bot.

Routes incoming messages to appropriate services.
Handles /start command with access control.
"""

import logging

from aiogram import Router, types
from aiogram.filters import Command

from config import config
from services.athlete_service import AthleteService

logger = logging.getLogger(__name__)

# Router for message handlers
message_router = Router()


def setup_message_handlers(dp, athlete_service: AthleteService):
    """Register message handlers with the dispatcher."""

    @message_router.message(Command("start"))
    async def handle_start(message: types.Message) -> None:
        """Handle /start command with access control."""
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"
        full_name = message.from_user.full_name or "User"

        # Admin check first
        if user_id == config.ADMIN_ID:
            await message.answer("🎯 Coach admin panel initialized")
            logger.info(f"Admin coach {user_id} started the bot")
            return

        # Check athlete access
        if athlete_service.has_access(user_id):
            info = athlete_service.get_access_info(user_id)
            days = info["days_remaining"] if info else 0
            
            await message.answer(
                f"✅ Training system access granted.\n\n"
                f"Welcome, {full_name}!\n"
                f"Subscription expires in {days} days."
            )
            logger.info(f"Athlete {user_id} accessed the bot")
        else:
            await message.answer(
                "⛔ Access not granted.\n\n"
                "Please contact your coach to get access."
            )
            logger.info(f"Unauthorized user {user_id} attempted access")
