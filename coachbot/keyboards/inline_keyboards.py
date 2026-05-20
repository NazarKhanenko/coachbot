"""
Inline keyboard builders for the bot.

Provides reusable keyboard constructors for consistent UI.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def workout_session_keyboard(session_id: str, current_index: int, total_exercises: int) -> InlineKeyboardMarkup:
    """Build navigation keyboard for workout session exercises (MVP)."""
    buttons = []

    # Navigation row
    nav_row = []
    
    # Previous exercise
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"workout_prev_{session_id}"))
    
    # Next exercise
    if current_index < total_exercises - 1:
        nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"workout_next_{session_id}"))
    
    if nav_row:
        buttons.append(nav_row)

    # Action row
    action_row = [
        InlineKeyboardButton(text="✅ Completed", callback_data=f"workout_complete_{session_id}"),
        InlineKeyboardButton(text="🆘 Need Help", callback_data=f"workout_help_{session_id}"),
    ]
    buttons.append(action_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workout_list_keyboard(workouts: list) -> InlineKeyboardMarkup:
    """Build a keyboard showing list of workouts."""
    buttons = []
    for workout in workouts:
        buttons.append(
            [InlineKeyboardButton(text=f"📋 {workout.title}", callback_data=f"workout_{workout.id}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def exercise_navigation_keyboard(workout_id: str, block_index: int, exercise_index: int, 
                                  total_blocks: int, total_exercises: int) -> InlineKeyboardMarkup:
    """Build navigation keyboard for exercises within a workout."""
    buttons = []

    # Navigation row
    nav_row = []
    
    # Previous block
    if block_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Block", callback_data=f"prev_block_{workout_id}_{block_index}"))
    
    # Next block
    if block_index < total_blocks - 1:
        nav_row.append(InlineKeyboardButton(text="Block ➡️", callback_data=f"next_block_{workout_id}_{block_index}"))
    
    if nav_row:
        buttons.append(nav_row)

    # Exercise navigation row
    ex_nav_row = []
    
    # Previous exercise
    if exercise_index > 0:
        ex_nav_row.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"prev_ex_{workout_id}_{exercise_index}"))
    
    # Next exercise
    if exercise_index < total_exercises - 1:
        ex_nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"next_ex_{workout_id}_{exercise_index}"))
    
    if ex_nav_row:
        buttons.append(ex_nav_row)

    # Action row
    action_row = [
        InlineKeyboardButton(text="✅ Done", callback_data=f"done_{workout_id}_{exercise_index}"),
        InlineKeyboardButton(text="❓ Help", callback_data=f"help_{workout_id}_{exercise_index}"),
    ]
    buttons.append(action_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_add_athlete_keyboard(coach_id: int, athlete_username: str) -> InlineKeyboardMarkup:
    """Build confirmation keyboard for adding an athlete."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data=f"confirm_add_{coach_id}_{athlete_username}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add_athlete"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def help_request_keyboard(workout_id: str, exercise_id: str) -> InlineKeyboardMarkup:
    """Build keyboard for help request actions."""
    buttons = [
        [InlineKeyboardButton(text="📹 Upload Video", callback_data=f"upload_video_{workout_id}_{exercise_id}")],
        [InlineKeyboardButton(text="💬 Send Message", callback_data=f"send_message_{workout_id}_{exercise_id}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data=f"back_to_exercise_{workout_id}_{exercise_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
