"""
Message handlers for the bot.

Routes incoming messages to appropriate services.
"""

import logging

from aiogram import Router, types
from aiogram.filters import Command

from models.entities import Coach
from services import CoachService

logger = logging.getLogger(__name__)

# Router for message handlers
message_router = Router()


@message_router.message(Command("start"))
async def handle_start(message: types.Message) -> None:
    """Handle /start command."""
    coach_service = CoachService()
    
    # Register user as coach (simplified - in production would check roles)
    coach = coach_service.register_coach(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "unknown",
    )
    
    await message.answer(
        f"👋 Welcome, Coach {coach.username}!\n\n"
        "I'm your coaching assistant. Here's what you can do:\n\n"
        "• /add_athlete - Add a new athlete\n"
        "• /athletes - View your athletes\n"
        "• /create_workout - Create a workout\n"
        "• /help - Show help message"
    )
    logger.info(f"User {message.from_user.id} started the bot")


@message_router.message(Command("add_athlete"))
async def handle_add_athlete(message: types.Message) -> None:
    """Handle /add_athlete command."""
    await message.answer(
        "📝 To add an athlete, please provide their Telegram username.\n\n"
        "Example: @john_doe\n\n"
        "Send the username now:"
    )


@message_router.message(Command("athletes"))
async def handle_list_athletes(message: types.Message) -> None:
    """Handle /athletes command."""
    coach_service = CoachService()
    coach_id = message.from_user.id
    
    athletes = coach_service.get_my_athletes(coach_id)
    
    if not athletes:
        await message.answer("📭 You don't have any athletes yet.\nUse /add_athlete to add one.")
        return
    
    athlete_list = "\n".join([f"• @{a.username}" for a in athletes])
    await message.answer(f"👥 Your athletes:\n\n{athlete_list}")


@message_router.message(Command("help"))
async def handle_help(message: types.Message) -> None:
    """Handle /help command."""
    await message.answer(
        "📖 **Coach Bot Help**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/add_athlete - Add a new athlete to your roster\n"
        "/athletes - List all your athletes\n"
        "/create_workout - Create a new workout\n"
        "/help - Show this help message\n\n"
        "**For Athletes:**\n"
        "Athletes will receive workouts with interactive buttons to:\n"
        "• Mark exercises as done ✅\n"
        "• Request help ❓\n"
        "• Upload videos 📹"
    )


@message_router.message()
async def handle_unknown_message(message: types.Message) -> None:
    """Handle unknown messages."""
    # In production, this would handle stateful conversations
    await message.answer(
        "🤔 I'm not sure what to do with that.\n"
        "Use /help to see available commands."
    )
