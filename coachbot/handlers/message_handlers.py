"""
Message handlers for the bot.

Routes incoming messages to appropriate services.
Minimal bootstrap - only /start command with admin check.
"""

import logging

from aiogram import Router, types
from aiogram.filters import Command

from config import get_config

logger = logging.getLogger(__name__)

# Router for message handlers
message_router = Router()


@message_router.message(Command("start"))
async def handle_start(message: types.Message) -> None:
    """Handle /start command with admin/athlete differentiation."""
    config = get_config()
    user_id = message.from_user.id
    
    if user_id == config.admin_id:
        await message.answer("Coach admin panel initialized")
        logger.info(f"Admin coach {user_id} started the bot")
    else:
        await message.answer("Athlete access not configured yet")
        logger.info(f"Athlete {user_id} attempted to start the bot")
