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
            await callback.answer("Already at first exercise.", show_alert=True)
            return
        
        session, exercise, total = result
        current_num = session.current_exercise_index + 1
        
        exercise_text = (
            f"Exercise {current_num}/{total}\n\n"
            f"**{exercise.title}**\n\n"
            f"{exercise.description}\n\n"
            f"Sets: {exercise.sets} | Reps: {exercise.reps}\n"
            f"Rest: {exercise.rest_seconds}s"
        )
        
        from keyboards.inline_keyboards import workout_session_keyboard
        keyboard = workout_session_keyboard(
            session_id=session.session_id,
            current_index=session.current_exercise_index,
            total_exercises=total,
        )
        
        await callback.message.edit_text(exercise_text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data.startswith("workout_next_"))
    async def handle_workout_next(callback: types.CallbackQuery) -> None:
        """Handle next exercise navigation."""
        session_id = callback.data.replace("workout_next_", "")
        
        result = workout_service.next_exercise(session_id)
        if not result:
            await callback.answer("Already at last exercise.", show_alert=True)
            return
        
        session, exercise, total = result
        current_num = session.current_exercise_index + 1
        
        exercise_text = (
            f"Exercise {current_num}/{total}\n\n"
            f"**{exercise.title}**\n\n"
            f"{exercise.description}\n\n"
            f"Sets: {exercise.sets} | Reps: {exercise.reps}\n"
            f"Rest: {exercise.rest_seconds}s"
        )
        
        from keyboards.inline_keyboards import workout_session_keyboard
        keyboard = workout_session_keyboard(
            session_id=session.session_id,
            current_index=session.current_exercise_index,
            total_exercises=total,
        )
        
        await callback.message.edit_text(exercise_text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data.startswith("workout_complete_"))
    async def handle_workout_complete(callback: types.CallbackQuery) -> None:
        """Handle workout completion."""
        session_id = callback.data.replace("workout_complete_", "")
        
        result = workout_service.get_current_exercise_by_session(session_id)
        if result:
            session, exercise, total = result
            # Check if this is the last exercise
            if session.current_exercise_index == total - 1:
                workout_service.complete_workout(session_id)
                await callback.message.edit_text(
                    "🎉 **Workout completed!**\n\n"
                    "Great job! Your coach will be notified of your completion."
                )
                await callback.answer("Workout completed!", show_alert=True)
                return
        
        # Not last exercise or session not found
        await callback.answer("Complete all exercises first!", show_alert=True)

    @callback_router.callback_query(lambda c: c.data.startswith("workout_help_"))
    async def handle_workout_help(callback: types.CallbackQuery) -> None:
        """Handle help request - notify admin."""
        session_id = callback.data.replace("workout_help_", "")
        
        # Get session info for help notification
        result = workout_service.get_current_exercise_by_session(session_id)
        if not result:
            await callback.answer("Session not found.", show_alert=True)
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
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Failed to send help notification to admin: {e}")
            await callback.answer("Could not notify coach. Please message directly.", show_alert=True)
            return
        
        await callback.answer("Coach has been notified!", show_alert=True)
        logger.info(f"Help request sent by athlete {athlete_id} for exercise {exercise.title}")

    @callback_router.callback_query(lambda c: c.data.startswith("workout_"))
    async def handle_workout_selected(callback: types.CallbackQuery) -> None:
        """Handle workout selection from list."""
        workout_id = callback.data.replace("workout_", "")
        
        # TODO: Fetch workout details and show first block/exercise
        await callback.message.edit_text(
            f"📋 Workout: {workout_id}\n\n"
            "Loading exercises...\n\n"
            "(Implementation pending)"
        )
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data.startswith("done_"))
    async def handle_exercise_done(callback: types.CallbackQuery) -> None:
        """Handle exercise marked as done."""
        parts = callback.data.replace("done_", "").split("_")
        # workout_id = parts[0]
        # exercise_index = parts[1]
        
        # TODO: Call ExerciseService.mark_exercise_done()
        await callback.answer("✅ Exercise marked as done!", show_alert=True)

    @callback_router.callback_query(lambda c: c.data.startswith("help_"))
    async def handle_exercise_help(callback: types.CallbackQuery) -> None:
        """Handle help request for an exercise."""
        parts = callback.data.replace("help_", "").split("_")
        # workout_id = parts[0]
        # exercise_index = parts[1]
        
        # TODO: Show help options (video upload, message)
        await callback.answer("❓ Help requested. Coach will be notified.", show_alert=True)

    @callback_router.callback_query(lambda c: c.data.startswith("confirm_add_"))
    async def handle_confirm_add_athlete(callback: types.CallbackQuery) -> None:
        """Handle confirmation of adding an athlete."""
        # Parse coach_id and athlete_username from callback data
        data = callback.data.replace("confirm_add_", "")
        # coach_id = int(parts[0])
        # athlete_username = parts[1]
        
        # TODO: Call CoachService.add_athlete()
        await callback.message.edit_text("✅ Athlete added successfully!")
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data == "cancel_add_athlete")
    async def handle_cancel_add_athlete(callback: types.CallbackQuery) -> None:
        """Handle cancellation of adding an athlete."""
        await callback.message.edit_text("❌ Adding athlete cancelled.")
        await callback.answer()

    @callback_router.callback_query(lambda c: c.data.startswith("prev_block_"))
    async def handle_prev_block(callback: types.CallbackQuery) -> None:
        """Handle navigation to previous block."""
        await callback.answer("Navigate to previous block (pending)")

    @callback_router.callback_query(lambda c: c.data.startswith("next_block_"))
    async def handle_next_block(callback: types.CallbackQuery) -> None:
        """Handle navigation to next block."""
        await callback.answer("Navigate to next block (pending)")

    @callback_router.callback_query(lambda c: c.data.startswith("prev_ex_"))
    async def handle_prev_exercise(callback: types.CallbackQuery) -> None:
        """Handle navigation to previous exercise."""
        await callback.answer("Navigate to previous exercise (pending)")

    @callback_router.callback_query(lambda c: c.data.startswith("next_ex_"))
    async def handle_next_exercise(callback: types.CallbackQuery) -> None:
        """Handle navigation to next exercise."""
        await callback.answer("Navigate to next exercise (pending)")
