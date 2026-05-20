"""
Callback query handlers for inline button interactions.

Handles workout navigation, exercise actions, and athlete management.
"""

import logging

from aiogram import Router, types
from aiogram.filters import StateFilter

logger = logging.getLogger(__name__)

# Router for callback handlers
callback_router = Router()


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
