"""
Inline keyboard builders for the bot.

Provides reusable keyboard constructors for consistent UI.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Build main admin panel keyboard."""
    buttons = [
        [InlineKeyboardButton(text="👥 Спортсмены", callback_data="admin_athletes")],
        [InlineKeyboardButton(text="🏋️ Тренировки", callback_data="admin_workouts")],
        [InlineKeyboardButton(text="📨 Запросы помощи", callback_data="admin_help_requests")],
        [InlineKeyboardButton(text="⚙️ Система", callback_data="admin_system")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_athletes_menu_keyboard() -> InlineKeyboardMarkup:
    """Build athletes management menu keyboard."""
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить спортсмена", callback_data="admin_add_athlete")],
        [InlineKeyboardButton(text="📋 Список спортсменов", callback_data="admin_list_athletes")],
        [InlineKeyboardButton(text="🔍 Найти спортсмена", callback_data="admin_find_athlete")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_back_to_athletes_keyboard() -> InlineKeyboardMarkup:
    """Build back to athletes menu keyboard."""
    buttons = [
        [InlineKeyboardButton(text="⬅️ В меню спортсменов", callback_data="admin_back_athletes")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_athlete_actions_keyboard(athlete_id: int) -> InlineKeyboardMarkup:
    """Build actions keyboard for a specific athlete."""
    buttons = [
        [InlineKeyboardButton(text="🏋️ Тренировка", callback_data=f"admin_athlete_workout_{athlete_id}")],
        [InlineKeyboardButton(text="⏸ Заморозить", callback_data=f"admin_athlete_freeze_{athlete_id}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"admin_athlete_remove_{athlete_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_workout_assign_keyboard(athlete_id: int) -> InlineKeyboardMarkup:
    """Build workout assignment keyboard."""
    buttons = [
        [InlineKeyboardButton(text="➕ Выдать демо-тренировку", callback_data=f"admin_assign_demo_{athlete_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_athletes")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_help_request_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """Build keyboard for help request actions."""
    buttons = [
        [InlineKeyboardButton(text="✅ Закрыть запрос", callback_data=f"admin_close_help_{request_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_system_keyboard() -> InlineKeyboardMarkup:
    """Build system panel keyboard."""
    buttons = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_system_refresh")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workout_session_keyboard(session_id: str, current_index: int, total_exercises: int) -> InlineKeyboardMarkup:
    """Build navigation keyboard for workout session exercises (MVP)."""
    buttons = []

    # Row 1: Back | Done
    nav_row = []
    
    # Previous exercise
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"workout_prev_{session_id}"))
    
    # Done button (always present)
    nav_row.append(InlineKeyboardButton(text="✅ Выполнил", callback_data=f"workout_done_{session_id}"))
    
    buttons.append(nav_row)

    # Row 2: Help
    buttons.append([InlineKeyboardButton(text="🆘 Нужна помощь", callback_data=f"workout_help_{session_id}")])

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
