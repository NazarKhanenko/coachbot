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
from services.workout_service import WorkoutService
from keyboards.inline_keyboards import workout_session_keyboard

logger = logging.getLogger(__name__)

# Router for message handlers
message_router = Router()


def setup_message_handlers(dp, athlete_service: AthleteService, workout_service: WorkoutService):
    """Register message handlers with the dispatcher."""

    @message_router.message(Command("workout"))
    async def handle_workout(message: types.Message) -> None:
        """Handle /workout command - show current exercise."""
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        
        # Admin can test workouts without being an athlete
        is_admin = user_id == config.ADMIN_ID
        
        if not is_admin and not athlete_service.has_access(user_id):
            await message.answer(
                "⛔ Access not granted.\n\n"
                "Please contact your coach to get access."
            )
            logger.info(f"Unauthorized user {user_id} attempted /workout")
            return

        # Get current exercise
        result = workout_service.get_current_exercise(user_id)
        if not result:
            await message.answer(
                "📭 No active workout session.\n\n"
                "Ask your coach to create a workout for you."
            )
            return

        session, exercise, total = result
        current_num = session.current_exercise_index + 1

        # Format exercise message
        exercise_text = (
            f"Exercise {current_num}/{total}\n\n"
            f"**{exercise.title}**\n\n"
            f"{exercise.description}\n\n"
            f"Sets: {exercise.sets} | Reps: {exercise.reps}\n"
            f"Rest: {exercise.rest_seconds}s"
        )

        keyboard = workout_session_keyboard(
            session_id=session.session_id,
            current_index=session.current_exercise_index,
            total_exercises=total,
        )

        await message.answer(exercise_text, parse_mode="Markdown", reply_markup=keyboard)
        logger.info(f"Athlete {user_id} viewed workout exercise {current_num}/{total}")

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
