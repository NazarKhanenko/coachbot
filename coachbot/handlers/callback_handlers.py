"""
Callback query handlers for inline button interactions.

Handles workout navigation, exercise actions, and athlete management.
"""

import logging

from aiogram import Router, types

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
        
        result = workout_service.previous_exercise(session_id)
        if not result:
            await callback.answer("Уже первое упражнение.", show_alert=True)
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
        
        await callback.message.edit_text(exercise_text, reply_markup=keyboard)
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data.startswith("workout_done_"))
    async def handle_workout_done(callback: types.CallbackQuery) -> None:
        """Handle exercise marked as done - auto advance or complete workout."""
        session_id = callback.data.replace("workout_done_", "")
        
        result = workout_service.get_current_exercise_by_session(session_id)
        if not result:
            await callback.answer("Сессия не найдена.", show_alert=True)
            return
        
        session, exercise, total = result
        current_num = session.current_exercise_index + 1
        
        # Check if this is the last exercise
        if current_num == total:
            # Complete entire workout
            workout_service.complete_workout(session_id)
            
            # Remove keyboard and show completion message
            await callback.message.edit_text(
                "🏁 Тренировка завершена\n\n"
                "Отличная работа.\n"
                "Тренер получил уведомление о завершении сессии."
            )
            await callback.answer("🏁 Тренировка завершена!", show_alert=True)
            logger.info(f"Athlete {callback.from_user.id} completed workout {session_id}")
            return
        
        # Not last exercise - check if video required
        if exercise.requires_video:
            # Show video request message
            video_request_text = (
                f"📹 Отправь видео выполнения упражнения\n\n"
                f"{exercise.title}"
            )
            
            from keyboards.inline_keyboards import workout_session_keyboard
            keyboard = workout_session_keyboard(
                session_id=session.session_id,
                current_index=session.current_exercise_index,
                total_exercises=total,
            )
            
            await callback.message.edit_text(video_request_text, reply_markup=keyboard)
            await callback.answer("📹 Ожидаем видео", show_alert=True)
            
            # Notify admin about video request
            athlete_username = callback.from_user.username or f"user_{callback.from_user.id}"
            try:
                await callback.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text=(
                        f"📹 Запрос видео\n\n"
                        f"👤 Игрок: @{athlete_username}\n"
                        f"🏃 Упражнение: {exercise.title}\n"
                        f"Тренировка: {session.title}"
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send video notification to admin: {e}")
            
            # Auto-advance after showing video request
            next_result = workout_service.next_exercise(session_id)
            if next_result:
                next_session, next_exercise, next_total = next_result
                next_num = next_session.current_exercise_index + 1
                
                next_exercise_text = format_exercise_card(next_exercise, next_num, next_total)
                
                next_keyboard = workout_session_keyboard(
                    session_id=next_session.session_id,
                    current_index=next_session.current_exercise_index,
                    total_exercises=next_total,
                )
                
                await callback.message.answer(next_exercise_text, reply_markup=next_keyboard)
            return
        
        # Normal exercise - just advance to next
        next_result = workout_service.next_exercise(session_id)
        if not next_result:
            await callback.answer("Ошибка перехода к следующему упражнению.", show_alert=True)
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
        
        await callback.message.edit_text(next_exercise_text, reply_markup=next_keyboard)
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data.startswith("workout_help_"))
    async def handle_workout_help(callback: types.CallbackQuery) -> None:
        """Handle help request - notify admin."""
        session_id = callback.data.replace("workout_help_", "")
        
        # Get session info for help notification
        result = workout_service.get_current_exercise_by_session(session_id)
        if not result:
            await callback.answer("Сессия не найдена.", show_alert=True)
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
            await callback.answer("Не удалось отправить запрос тренеру.", show_alert=True)
            return
        
        # Confirm to athlete
        await callback.answer("🆘 Запрос отправлен тренеру.", show_alert=True)
        logger.info(f"Help request sent by athlete {athlete_id} for exercise {exercise.title}")

    @callback_router.callback_query(lambda c: c.data.startswith("workout_"))
    async def handle_workout_selected(callback: types.CallbackQuery) -> None:
        """Handle workout selection from list."""
        workout_id = callback.data.replace("workout_", "")
        
        # TODO: Fetch workout details and show first block/exercise
        await callback.message.edit_text(
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
        await callback.message.edit_text("✅ Спортсмен добавлен")
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data == "cancel_add_athlete")
    async def handle_cancel_add_athlete(callback: types.CallbackQuery) -> None:
        """Handle cancellation of adding an athlete."""
        await callback.message.edit_text("❌ Добавление спортсмена отменено.")
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
    lines = [
        f"🏃 {exercise.title}",
        "",
        f"📋 Описание:",
        f"{exercise.description}",
        "",
        f"🔁 Подходы: {exercise.sets}",
        f"📈 Повторения: {exercise.reps}",
        f"⏱ Отдых: {exercise.rest_seconds} сек",
    ]
    
    if exercise.video_url:
        lines.extend([
            "",
            f"📹 Видео:",
            f"{exercise.video_url}",
        ])
    
    lines.extend([
        "",
        f"Упражнение {current_num}/{total}",
    ])
    
    return "\n".join(lines)
