"""
Message handlers for the bot.

Routes incoming messages to appropriate services.
Handles /start command with access control.
"""

import logging

from aiogram import F, Router, types
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

    # Media handler MUST be registered AFTER command handlers
    # to ensure commands have priority
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

    @message_router.message(Command("workout"))
    async def handle_workout(message: types.Message) -> None:
        """Handle /workout command - show current exercise."""
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        
        # Admin can test workouts without being an athlete
        is_admin = user_id == config.ADMIN_ID
        
        if not is_admin and not athlete_service.has_access(user_id):
            await message.answer(
                "🔒 Доступ к системе не активирован."
            )
            logger.info(f"Unauthorized user {user_id} attempted /workout")
            return

        # Get current exercise
        result = workout_service.get_current_exercise(user_id)
        if not result:
            await message.answer(
                "❌ У тебя нет активной тренировки."
            )
            return

        session, exercise, total = result
        current_num = session.current_exercise_index + 1

        # Format exercise card with clean layout
        from handlers.callback_handlers import format_exercise_card
        exercise_text = format_exercise_card(exercise, current_num, total)

        keyboard = workout_session_keyboard(
            session_id=session.session_id,
            current_index=session.current_exercise_index,
            total_exercises=total,
        )

        await send_exercise_with_video(message.bot, message.chat.id, exercise_text, exercise, keyboard)
        logger.info(f"Athlete {user_id} viewed workout exercise {current_num}/{total}")

    @message_router.message(
        (F.video | F.document | F.text)
        & (~F.command)  # Exclude commands
    )
    async def handle_media_message(message: types.Message) -> None:
        """Handle media submissions (video/file/link) during waiting_video state."""
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        
        # Check if user has an active workout in waiting_video state
        result = workout_service.get_current_exercise(user_id)
        if not result:
            return
        
        session, exercise, total = result
        
        # Only process if exercise is in waiting_video state
        if exercise.state != "waiting_video":
            return
        
        # Determine what type of media was sent
        media_type = None
        media_info = ""
        
        if message.video:
            media_type = "video"
            media_info = f"Video file_id: {message.video.file_id}"
        elif message.document:
            media_type = "document"
            media_info = f"Document file_id: {message.document.file_id}"
        elif message.text:
            # Check if it's a valid URL (http://, https://, or t.me/)
            text = message.text.strip()
            if text.startswith(("http://", "https://", "t.me/")):
                media_type = "link"
                media_info = f"Link: {text}"
            else:
                # Not a valid link, ignore
                return
        
        if not media_type:
            return
        
        # Update exercise state to completed
        workout_service.update_exercise_state(session.session_id, session.current_exercise_index, "completed")
        
        # Send confirmation to athlete
        await message.answer("✅ Видео отправлено тренеру.")
        
        # Notify admin about video submission
        notification = workout_service.notify_video_submission(
            athlete_id=user_id,
            athlete_username=username,
            session=session,
            exercise=exercise,
        )
        
        try:
            await message.bot.send_message(
                chat_id=config.ADMIN_ID,
                text=f"{notification}\n\n📎 {media_info}",
            )
        except Exception as e:
            logger.error(f"Failed to send video submission notification to admin: {e}")
        
        # Auto-advance to next exercise
        next_result = workout_service.next_exercise(session.session_id)
        if next_result:
            next_session, next_exercise, next_total = next_result
            next_num = next_session.current_exercise_index + 1
            
            from handlers.callback_handlers import format_exercise_card
            next_exercise_text = format_exercise_card(next_exercise, next_num, next_total)
            
            next_keyboard = workout_session_keyboard(
                session_id=next_session.session_id,
                current_index=next_session.current_exercise_index,
                total_exercises=next_total,
            )
            
            await send_exercise_with_video(
                message.bot, 
                message.chat.id, 
                next_exercise_text, 
                next_exercise, 
                next_keyboard
            )
        else:
            # No more exercises - complete workout
            workout_service.complete_workout(session.session_id)
            await message.answer(
                "🏁 Тренировка завершена\n\n"
                "Отличная работа.\n"
                "Тренер получил уведомление о завершении сессии."
            )
        
        logger.info(f"Athlete {user_id} submitted {media_type} for exercise {exercise.title}")


async def send_exercise_with_video(bot, chat_id: int, text: str, exercise, keyboard):
    """Send exercise card with embedded Telegram video if available."""
    if exercise.telegram_file_id:
        # Send video with caption
        await bot.send_video(
            chat_id=chat_id,
            video=exercise.telegram_file_id,
            caption=text,
            reply_markup=keyboard,
        )
    else:
        # Send regular text message
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
