"""
Callback query handlers for inline button interactions.

Handles workout navigation, exercise actions, and athlete management.
"""

import logging

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest

from config import config
from services.workout_service import WorkoutService

logger = logging.getLogger(__name__)

# Router for callback handlers
callback_router = Router()


def setup_callback_handlers(dp: Router, workout_service: WorkoutService):
    """Register callback handlers with the router."""

    @callback_router.callback_query(lambda c: c.data.startswith("workout_prev_"))
    async def handle_workout_prev(callback: types.CallbackQuery) -> None:
        """Handle previous exercise navigation."""
        session_id = callback.data.replace("workout_prev_", "")
        
        # Answer callback immediately to prevent duplicate processing
        await callback.answer()
        
        result = workout_service.previous_exercise(session_id)
        if not result:
            await callback.message.answer("Уже первое упражнение.", show_alert=True)
            return
        
        session, exercise, total = result
        current_num = session.current_exercise_index + 1
        
        # Format exercise card with clean layout
        exercise_text = format_exercise_card(exercise, current_num, total)
        
        from keyboards.inline_keyboards import workout_session_keyboard
        keyboard = workout_session_keyboard(
            session_id=session.session_id,
            current_index=session.current_exercise_index,
            total_exercises=total,
        )
        
        # Try to edit existing message, fallback to sending new one
        await update_workout_message(
            bot=callback.bot,
            session_id=session_id,
            chat_id=callback.message.chat.id,
            text=exercise_text,
            keyboard=keyboard,
            workout_service=workout_service,
        )

    @callback_router.callback_query(lambda c: c.data.startswith("workout_done_"))
    async def handle_workout_done(callback: types.CallbackQuery) -> None:
        """Handle exercise marked as done - auto advance or complete workout."""
        session_id = callback.data.replace("workout_done_", "")
        
        # Answer callback immediately to prevent duplicate processing
        await callback.answer()
        
        result = workout_service.get_current_exercise_by_session(session_id)
        if not result:
            await callback.message.answer("Сессия не найдена.", show_alert=True)
            return
        
        session, exercise, total = result
        current_num = session.current_exercise_index + 1
        athlete_id = callback.from_user.id
        athlete_username = callback.from_user.username or f"user_{athlete_id}"
        
        # Check if this is the last exercise
        if current_num == total:
            # Complete entire workout
            workout_service.complete_workout(session_id)
            workout_service.clear_active_message(session_id)
            
            # Remove keyboard and show completion message
            completion_text = (
                "🏁 Тренировка завершена\n\n"
                "Отличная работа.\n"
                "Тренер получил уведомление о завершении сессии."
            )
            
            try:
                await callback.message.edit_text(completion_text)
            except TelegramBadRequest:
                await callback.message.answer(completion_text)
            
            logger.info(f"Athlete {athlete_id} completed workout {session_id}")
            return
        
        # Check exercise state for video flow
        if exercise.state == "waiting_video":
            # Already waiting for video, ignore duplicate clicks
            return
        
        # Not last exercise - check if video required
        if exercise.requires_video and exercise.state == "pending":
            # Update state to waiting_video
            workout_service.update_exercise_state(session_id, session.current_exercise_index, "waiting_video")
            
            # Show video request message (edit current message)
            video_request_text = (
                f"📹 Отправь видео выполнения упражнения\n\n"
                f"🏃 {exercise.title}\n\n"
                f"Поддерживаются:\n"
                f"• Видео Telegram\n"
                f"• Файл\n"
                f"• Ссылка"
            )
            
            # Remove keyboard while waiting for video
            try:
                await callback.message.edit_text(video_request_text)
                # Store message reference for future edits
                workout_service.set_active_message(session_id, callback.message.chat.id, callback.message.message_id)
            except TelegramBadRequest:
                new_msg = await callback.message.answer(video_request_text)
                workout_service.set_active_message(session_id, new_msg.chat.id, new_msg.message_id)
            
            # Notify admin about video request (only once)
            try:
                await callback.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text=(
                        f"📹 Запрос видео\n\n"
                        f"👤 Игрок: @{athlete_username}\n"
                        f"🏃 Упражнение: {exercise.title}\n"
                        f"🏋️ Тренировка: {session.title}"
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send video notification to admin: {e}")
            
            # Do NOT auto-advance yet - wait for media
            return
        
        # Normal exercise or already completed video requirement - just advance to next
        next_result = workout_service.next_exercise(session_id)
        if not next_result:
            await callback.message.answer("Ошибка перехода к следующему упражнению.", show_alert=True)
            return
        
        next_session, next_exercise, next_total = next_result
        next_num = next_session.current_exercise_index + 1
        
        next_exercise_text = format_exercise_card(next_exercise, next_num, next_total)
        
        from keyboards.inline_keyboards import workout_session_keyboard
        next_keyboard = workout_session_keyboard(
            session_id=next_session.session_id,
            current_index=next_session.current_exercise_index,
            total_exercises=next_total,
        )
        
        # Try to edit existing message, fallback to sending new one
        await update_workout_message(
            bot=callback.bot,
            session_id=session_id,
            chat_id=callback.message.chat.id,
            text=next_exercise_text,
            keyboard=next_keyboard,
            workout_service=workout_service,
        )

    @callback_router.callback_query(lambda c: c.data.startswith("workout_help_"))
    async def handle_workout_help(callback: types.CallbackQuery) -> None:
        """Handle help request - notify admin."""
        session_id = callback.data.replace("workout_help_", "")
        
        # Answer callback immediately to prevent duplicate processing
        await callback.answer()
        
        # Get session info for help notification
        result = workout_service.get_current_exercise_by_session(session_id)
        if not result:
            await callback.message.answer("Сессия не найдена.", show_alert=True)
            return
        
        session, exercise, total = result
        athlete_id = callback.from_user.id
        athlete_username = callback.from_user.username or f"user_{athlete_id}"
        
        # Generate and send notification to admin
        notification = workout_service.notify_help_request(
            athlete_id=athlete_id,
            athlete_username=athlete_username,
            session=session,
            exercise=exercise,
        )
        
        try:
            await callback.bot.send_message(
                chat_id=config.ADMIN_ID,
                text=notification,
            )
        except Exception as e:
            logger.error(f"Failed to send help notification to admin: {e}")
            await callback.message.answer("Не удалось отправить запрос тренеру.", show_alert=True)
            return
        
        # Confirm to athlete using answer() to avoid cluttering chat
        await callback.message.answer("🆘 Запрос отправлен тренеру.", show_alert=False)
        logger.info(f"Help request sent by athlete {athlete_id} for exercise {exercise.title}")

    @callback_router.callback_query(lambda c: c.data.startswith("workout_"))
    async def handle_workout_selected(callback: types.CallbackQuery) -> None:
        """Handle workout selection from list."""
        workout_id = callback.data.replace("workout_", "")
        
        # TODO: Fetch workout details and show first block/exercise
        try:
            await callback.message.edit_text(
                f"📋 Тренировка: {workout_id}\n\n"
                f"Загрузка упражнений...\n\n"
                f"(В разработке)"
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"📋 Тренировка: {workout_id}\n\n"
                f"Загрузка упражнений...\n\n"
                f"(В разработке)"
            )
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data.startswith("done_"))
    async def handle_exercise_done(callback: types.CallbackQuery) -> None:
        """Handle exercise marked as done."""
        parts = callback.data.replace("done_", "").split("_")
        # workout_id = parts[0]
        # exercise_index = parts[1]
        
        # TODO: Call ExerciseService.mark_exercise_done()
        await callback.answer("✅ Упражнение выполнено!", show_alert=True)

    @callback_router.callback_query(lambda c: c.data.startswith("help_"))
    async def handle_exercise_help(callback: types.CallbackQuery) -> None:
        """Handle help request for an exercise."""
        parts = callback.data.replace("help_", "").split("_")
        # workout_id = parts[0]
        # exercise_index = parts[1]
        
        # TODO: Show help options (video upload, message)
        await callback.answer("❓ Запрос помощи отправлен тренеру.", show_alert=True)

    @callback_router.callback_query(lambda c: c.data.startswith("confirm_add_"))
    async def handle_confirm_add_athlete(callback: types.CallbackQuery) -> None:
        """Handle confirmation of adding an athlete."""
        # Parse coach_id and athlete_username from callback data
        data = callback.data.replace("confirm_add_", "")
        # coach_id = int(parts[0])
        # athlete_username = parts[1]
        
        # TODO: Call CoachService.add_athlete()
        try:
            await callback.message.edit_text("✅ Спортсмен добавлен")
        except TelegramBadRequest:
            await callback.message.answer("✅ Спортсмен добавлен")
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data == "cancel_add_athlete")
    async def handle_cancel_add_athlete(callback: types.CallbackQuery) -> None:
        """Handle cancellation of adding an athlete."""
        try:
            await callback.message.edit_text("❌ Добавление спортсмена отменено.")
        except TelegramBadRequest:
            await callback.message.answer("❌ Добавление спортсмена отменено.")
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data.startswith("prev_block_"))
    async def handle_prev_block(callback: types.CallbackQuery) -> None:
        """Handle navigation to previous block."""
        await callback.answer("Переход к предыдущему блоку (в разработке)")

    @callback_router.callback_query(lambda c: c.data.startswith("next_block_"))
    async def handle_next_block(callback: types.CallbackQuery) -> None:
        """Handle navigation to next block."""
        await callback.answer("Переход к следующему блоку (в разработке)")

    @callback_router.callback_query(lambda c: c.data.startswith("prev_ex_"))
    async def handle_prev_exercise(callback: types.CallbackQuery) -> None:
        """Handle navigation to previous exercise."""
        await callback.answer("Переход к предыдущему упражнению (в разработке)")

    @callback_router.callback_query(lambda c: c.data.startswith("next_ex_"))
    async def handle_next_exercise(callback: types.CallbackQuery) -> None:
        """Handle navigation to next exercise."""
        await callback.answer("Переход к следующему упражнению (в разработке)")


def format_exercise_card(exercise, current_num: int, total: int) -> str:
    """Format exercise card with clean Telegram-friendly layout."""
    # Title already includes emoji from workout_service
    lines = [
        f"{exercise.title}",
        "",
        f"📋 Описание:",
        f"{exercise.description}",
        "",
        f"🔁 Подходы: {exercise.sets}",
        f"📈 Повторения: {exercise.reps}",
        f"⏱ Отдых: {exercise.rest_seconds} сек",
    ]
    
    # Show embedded video if available, otherwise show URL
    if exercise.telegram_file_id:
        lines.extend([
            "",
            f"📹 Видео:",
            f"(Telegram видео)",
        ])
    elif exercise.video_url:
        lines.extend([
            "",
            f"📹 Видео:",
            f"{exercise.video_url}",
        ])
    
    # Show video requirement indicator
    if exercise.requires_video and exercise.state == "pending":
        lines.extend([
            "",
            f"📹 Требуется видеоотчёт",
        ])
    
    lines.extend([
        "",
        f"Упражнение {current_num}/{total}",
    ])
    
    return "\n".join(lines)


async def update_workout_message(
    bot,
    session_id: str,
    chat_id: int,
    text: str,
    keyboard,
    workout_service: WorkoutService,
) -> None:
    """Update workout message with fallback logic.
    
    Tries to edit the stored active message.
    If edit fails (message deleted/too old), sends a fresh message.
    """
    # Get stored message reference
    active_msg = workout_service.get_active_message(session_id)
    
    if active_msg:
        stored_chat_id, stored_message_id = active_msg
        try:
            await bot.edit_message_text(
                chat_id=stored_chat_id,
                message_id=stored_message_id,
                text=text,
                reply_markup=keyboard,
            )
            logger.debug(f"[TRACE] Updated workout message {stored_message_id}")
            return
        except TelegramBadRequest as e:
            logger.warning(f"Edit failed for message {stored_message_id}: {e}. Sending fresh message.")
    
    # Fallback: send new message and store reference
    new_msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
    )
    workout_service.set_active_message(session_id, new_msg.chat.id, new_msg.message_id)
    logger.debug(f"[TRACE] Sent new workout message {new_msg.message_id}")
