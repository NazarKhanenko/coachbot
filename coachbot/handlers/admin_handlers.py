"""Admin-only command handlers for athlete management with inline button UI."""
import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from config import config
from services.athlete_service import AthleteService
from services.workout_service import WorkoutService
from keyboards.inline_keyboards import (
    admin_main_keyboard,
    admin_athletes_menu_keyboard,
    admin_back_to_athletes_keyboard,
    admin_athlete_actions_keyboard,
    admin_workout_assign_keyboard,
    admin_help_request_keyboard,
    admin_system_keyboard,
    admin_workouts_keyboard,
    admin_weekly_plan_keyboard,
    admin_back_to_workouts_keyboard,
    admin_athlete_success_keyboard,
)

logger = logging.getLogger(__name__)

admin_router = Router()

# Lightweight in-memory state for admin flows (no FSM framework)
# Structure: {admin_id: {"state": str, "data": dict}}
_admin_state: dict[int, dict] = {}

# In-memory help requests storage (for MVP)
# Structure: {request_id: {"athlete_id": int, "athlete_username": str, "exercise": str, "time": str}}
_help_requests: dict[int, dict] = {}
_help_request_counter = 0


def setup_admin_handlers(dp: Router, athlete_service: AthleteService, workout_service: WorkoutService):
    """Register admin handlers with the router."""
    logger.info("[ADMIN] Setting up admin handlers with inline UI")

    # Store services in router data for callback handlers
    dp["athlete_service"] = athlete_service
    dp["workout_service"] = workout_service

    @admin_router.message(Command("start"))
    async def cmd_start_admin(message: Message):
        """Handle /start for admin - show main admin panel."""
        if message.from_user.id != config.ADMIN_ID:
            return  # Let message_handlers handle non-admin users
        
        await message.answer("🎛 Панель тренера", reply_markup=admin_main_keyboard())
        logger.info(f"Admin {message.from_user.id} opened main admin panel")

    @admin_router.callback_query(F.data == "admin_back_main")
    async def cb_admin_back_main(callback: CallbackQuery):
        """Return to main admin panel."""
        await callback.answer()
        try:
            await callback.message.edit_text("🎛 Панель тренера", reply_markup=admin_main_keyboard())
        except TelegramBadRequest:
            await callback.message.answer("🎛 Панель тренера", reply_markup=admin_main_keyboard())

    @admin_router.callback_query(F.data == "admin_athletes")
    async def cb_admin_athletes(callback: CallbackQuery):
        """Open athletes management menu."""
        await callback.answer()
        try:
            await callback.message.edit_text("👥 Управление спортсменами", reply_markup=admin_athletes_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer("👥 Управление спортсменами", reply_markup=admin_athletes_menu_keyboard())

    @admin_router.callback_query(F.data == "admin_add_athlete")
    async def cb_admin_add_athlete(callback: CallbackQuery):
        """Start add athlete flow - ask for Telegram ID."""
        await callback.answer()
        _admin_state[callback.from_user.id] = {"state": "waiting_athlete_id", "data": {}}
        try:
            await callback.message.edit_text(
                "Введи Telegram ID спортсмена\n\n⬅️ /cancel - отмена",
                reply_markup=admin_back_to_athletes_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "Введи Telegram ID спортсмена\n\n⬅️ /cancel - отмена",
                reply_markup=admin_back_to_athletes_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_back_athletes")
    async def cb_admin_back_athletes(callback: CallbackQuery):
        """Return to athletes menu."""
        await callback.answer()
        # Clear any pending state
        _admin_state.pop(callback.from_user.id, None)
        try:
            await callback.message.edit_text("👥 Управление спортсменами", reply_markup=admin_athletes_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer("👥 Управление спортсменами", reply_markup=admin_athletes_menu_keyboard())

    @admin_router.callback_query(F.data == "admin_list_athletes")
    async def cb_admin_list_athletes(callback: CallbackQuery):
        """Show list of athletes with actions."""
        await callback.answer()
        athlete_service: AthleteService = callback.bot.dispatcher["athlete_service"]
        
        athletes = athlete_service.list_athletes()
        
        if not athletes:
            try:
                await callback.message.edit_text(
                    "📭 Спортсменов пока нет.",
                    reply_markup=admin_back_to_athletes_keyboard(),
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    "📭 Спортсменов пока нет.",
                    reply_markup=admin_back_to_athletes_keyboard(),
                )
            return
        
        # Build compact athlete list with individual action buttons
        lines = ["📋 Список спортсменов:", ""]
        keyboard_buttons = []
        
        for athlete in athletes:
            status_icon = "🟢" if athlete.active and athlete.is_subscription_valid() else "🔴"
            days = athlete.days_remaining()
            lines.append(f"{status_icon} {athlete.telegram_id}")
            lines.append(f"⏳ {days} дней")
            lines.append("")
            
            # Add action buttons for this athlete
            keyboard_buttons.append([InlineKeyboardButton(text=f"🏋️ Тренировка | {athlete.telegram_id}", callback_data=f"admin_athlete_workout_{athlete.telegram_id}")])
            keyboard_buttons.append([InlineKeyboardButton(text=f"⏸ Заморозить | {athlete.telegram_id}", callback_data=f"admin_athlete_freeze_{athlete.telegram_id}")])
            keyboard_buttons.append([InlineKeyboardButton(text=f"❌ Удалить | {athlete.telegram_id}", callback_data=f"admin_athlete_remove_{athlete.telegram_id}")])
        
        # Add back button
        keyboard_buttons.append([InlineKeyboardButton(text="⬅️ В меню спортсменов", callback_data="admin_back_athletes")])
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        try:
            await callback.message.edit_text("\n".join(lines), reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer("\n".join(lines), reply_markup=keyboard)

    @admin_router.callback_query(lambda c: c.data.startswith("admin_athlete_workout_"))
    async def cb_admin_athlete_workout(callback: CallbackQuery):
        """Show workout assignment options for an athlete."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_athlete_workout_", ""))
        
        try:
            await callback.message.edit_text(
                f"🏋️ Тренировка для спортсмена {athlete_id}",
                reply_markup=admin_workout_assign_keyboard(athlete_id),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"🏋️ Тренировка для спортсмена {athlete_id}",
                reply_markup=admin_workout_assign_keyboard(athlete_id),
            )

    @admin_router.callback_query(lambda c: c.data.startswith("admin_assign_demo_"))
    async def cb_admin_assign_demo(callback: CallbackQuery):
        """Assign demo workout to athlete."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_assign_demo_", ""))
        workout_service: WorkoutService = callback.bot.dispatcher["workout_service"]
        athlete_service: AthleteService = callback.bot.dispatcher["athlete_service"]
        
        # Check if athlete exists and is active
        athlete = athlete_service.get_athlete(athlete_id)
        if not athlete:
            try:
                await callback.message.edit_text(f"❌ Спортсмен {athlete_id} не найден.", reply_markup=admin_back_to_athletes_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(f"❌ Спортсмен {athlete_id} не найден.", reply_markup=admin_back_to_athletes_keyboard())
            return
        
        if not athlete.active or not athlete.is_subscription_valid():
            try:
                await callback.message.edit_text(f"❌ Спортсмен {athlete_id} не активен.", reply_markup=admin_back_to_athletes_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(f"❌ Спортсмен {athlete_id} не активен.", reply_markup=admin_back_to_athletes_keyboard())
            return
        
        # Create demo workout
        session = workout_service.create_demo_workout(athlete_id=athlete_id)
        
        try:
            await callback.message.edit_text(
                f"✅ Тренировка выдана спортсмену {athlete_id}\n\n"
                f"📋 Название: {session.title}\n"
                f"🏋️ Упражнений: {len(session.exercises)}\n\n"
                f"Спортсмен может начать с /workout",
                reply_markup=admin_back_to_athletes_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"✅ Тренировка выдана спортсмену {athlete_id}\n\n"
                f"📋 Название: {session.title}\n"
                f"🏋️ Упражнений: {len(session.exercises)}\n\n"
                f"Спортсмен может начать с /workout",
                reply_markup=admin_back_to_athletes_keyboard(),
            )
        
        logger.info(f"Demo workout assigned to athlete {athlete_id} by admin")

    @admin_router.callback_query(lambda c: c.data.startswith("admin_athlete_freeze_"))
    async def cb_admin_athlete_freeze(callback: CallbackQuery):
        """Freeze (deactivate) an athlete."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_athlete_freeze_", ""))
        athlete_service: AthleteService = callback.bot.dispatcher["athlete_service"]
        
        athlete = athlete_service.get_athlete(athlete_id)
        if athlete:
            athlete.active = False
        
        try:
            await callback.message.edit_text(
                f"⏸ Спортсмен {athlete_id} заморожен.",
                reply_markup=admin_back_to_athletes_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"⏸ Спортсмен {athlete_id} заморожен.",
                reply_markup=admin_back_to_athletes_keyboard(),
            )

    @admin_router.callback_query(lambda c: c.data.startswith("admin_athlete_remove_"))
    async def cb_admin_athlete_remove(callback: CallbackQuery):
        """Remove (deactivate) an athlete."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_athlete_remove_", ""))
        athlete_service: AthleteService = callback.bot.dispatcher["athlete_service"]
        
        athlete_service.remove_athlete(athlete_id)
        
        try:
            await callback.message.edit_text(
                f"❌ Спортсмен {athlete_id} удалён.",
                reply_markup=admin_back_to_athletes_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"❌ Спортсмен {athlete_id} удалён.",
                reply_markup=admin_back_to_athletes_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_workouts")
    async def cb_admin_workouts(callback: CallbackQuery):
        """Show workouts categories panel."""
        await callback.answer()
        try:
            await callback.message.edit_text(
                "🏋️ Тренировки\n\nВыберите категорию:",
                reply_markup=admin_workouts_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "🏋️ Тренировки\n\nВыберите категорию:",
                reply_markup=admin_workouts_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_back_workouts")
    async def cb_admin_back_workouts(callback: CallbackQuery):
        """Return to workouts menu from sub-sections."""
        await callback.answer()
        try:
            await callback.message.edit_text(
                "🏋️ Тренировки\n\nВыберите категорию:",
                reply_markup=admin_workouts_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "🏋️ Тренировки\n\nВыберите категорию:",
                reply_markup=admin_workouts_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_workout_speed_power")
    async def cb_admin_workout_speed_power(callback: CallbackQuery):
        """Assign demo workout for speed/power category."""
        await callback.answer()
        # This connects to existing demo workout flow
        # For now, show message that admin needs to select athlete first
        try:
            await callback.message.edit_text(
                "⚡ Скорость и мощность\n\n"
                "Сначала выберите спортсмена из списка:\n"
                "👥 Спортсмены → 📋 Список спортсменов",
                reply_markup=admin_back_to_workouts_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "⚡ Скорость и мощность\n\n"
                "Сначала выберите спортсмена из списка:\n"
                "👥 Спортсмены → 📋 Список спортсменов",
                reply_markup=admin_back_to_workouts_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_workout_placeholder")
    async def cb_admin_workout_placeholder(callback: CallbackQuery):
        """Show placeholder for workout categories in development."""
        await callback.answer()
        try:
            await callback.message.edit_text(
                "🚧 Раздел в разработке\n\n"
                "Функционал будет добавлен в следующей версии.",
                reply_markup=admin_back_to_workouts_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "🚧 Раздел в разработке\n\n"
                "Функционал будет добавлен в следующей версии.",
                reply_markup=admin_back_to_workouts_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_weekly_plan")
    async def cb_admin_weekly_plan(callback: CallbackQuery):
        """Show weekly plan placeholder foundation."""
        await callback.answer()
        text = (
            "📅 Система недельного планирования\n\n"
            "Будущий функционал:\n"
            "• расписание недели\n"
            "• матчи\n"
            "• командные тренировки\n"
            "• индивидуальные тренировки\n"
            "• school/time management\n"
            "• intake planner"
        )
        try:
            await callback.message.edit_text(text, reply_markup=admin_weekly_plan_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=admin_weekly_plan_keyboard())

    @admin_router.callback_query(F.data == "admin_help_requests")
    async def cb_admin_help_requests(callback: CallbackQuery):
        """Show help requests panel."""
        await callback.answer()
        
        if not _help_requests:
            try:
                await callback.message.edit_text(
                    "📨 Запросы помощи\n\nНет активных запросов.",
                    reply_markup=admin_back_to_athletes_keyboard(),
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    "📨 Запросы помощи\n\nНет активных запросов.",
                    reply_markup=admin_back_to_athletes_keyboard(),
                )
            return
        
        # Show latest help request
        latest_id = max(_help_requests.keys())
        req = _help_requests[latest_id]
        
        text = (
            "📨 Запросы помощи\n\n"
            f"👤 @{req['athlete_username']}\n"
            f"🏃 {req['exercise']}\n"
            f"🕒 {req['time']}"
        )
        
        try:
            await callback.message.edit_text(text, reply_markup=admin_help_request_keyboard(latest_id))
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=admin_help_request_keyboard(latest_id))

    @admin_router.callback_query(lambda c: c.data.startswith("admin_close_help_"))
    async def cb_admin_close_help(callback: CallbackQuery):
        """Close a help request and return to main panel."""
        await callback.answer()
        request_id = int(callback.data.replace("admin_close_help_", ""))
        
        _help_requests.pop(request_id, None)
        
        try:
            await callback.message.edit_text(
                "✅ Запрос закрыт.",
                reply_markup=admin_back_to_athletes_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "✅ Запрос закрыт.",
                reply_markup=admin_back_to_athletes_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_system")
    async def cb_admin_system(callback: CallbackQuery):
        """Show system panel with stats."""
        await callback.answer()
        athlete_service: AthleteService = callback.bot.dispatcher["athlete_service"]
        workout_service: WorkoutService = callback.bot.dispatcher["workout_service"]
        
        athletes = athlete_service.list_athletes()
        active_count = sum(1 for a in athletes if a.active and a.is_subscription_valid())
        
        # Count active workouts (simplified - just count sessions in storage)
        active_workouts = len(workout_service.storage._sessions)
        
        text = (
            "⚙️ Система\n\n"
            f"👥 Активных спортсменов: {active_count}\n"
            f"🏋️ Активных тренировок: {active_workouts}\n"
            f"⏱ Uptime: (placeholder)"
        )
        
        try:
            await callback.message.edit_text(text, reply_markup=admin_system_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=admin_system_keyboard())

    @admin_router.callback_query(F.data == "admin_system_refresh")
    async def cb_admin_system_refresh(callback: CallbackQuery):
        """Refresh system panel."""
        await callback.answer()
        athlete_service: AthleteService = callback.bot.dispatcher["athlete_service"]
        workout_service: WorkoutService = callback.bot.dispatcher["workout_service"]
        
        athletes = athlete_service.list_athletes()
        active_count = sum(1 for a in athletes if a.active and a.is_subscription_valid())
        active_workouts = len(workout_service.storage._sessions)
        
        text = (
            "⚙️ Система\n\n"
            f"👥 Активных спортсменов: {active_count}\n"
            f"🏋️ Активных тренировок: {active_workouts}\n"
            f"⏱ Uptime: (placeholder)"
        )
        
        try:
            await callback.message.edit_text(text, reply_markup=admin_system_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=admin_system_keyboard())

    @admin_router.callback_query(F.data == "admin_find_athlete")
    async def cb_admin_find_athlete(callback: CallbackQuery):
        """Find athlete placeholder."""
        await callback.answer()
        _admin_state[callback.from_user.id] = {"state": "waiting_find_query", "data": {}}
        try:
            await callback.message.edit_text(
                "Введи Telegram ID для поиска\n\n⬅️ /cancel - отмена",
                reply_markup=admin_back_to_athletes_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "Введи Telegram ID для поиска\n\n⬅️ /cancel - отмена",
                reply_markup=admin_back_to_athletes_keyboard(),
            )

    @admin_router.message(lambda m: m.from_user.id == config.ADMIN_ID and m.text == "/cancel")
    async def cmd_cancel(message: Message):
        """Cancel current admin flow."""
        _admin_state.pop(message.from_user.id, None)
        await message.answer("❌ Отменено.", reply_markup=admin_athletes_menu_keyboard())

    @admin_router.message(lambda m: m.from_user.id == config.ADMIN_ID)
    async def handle_admin_input(message: Message):
        """Handle admin text input for multi-step flows."""
        admin_id = message.from_user.id
        
        if admin_id not in _admin_state:
            return  # Not in a flow
        
        state_info = _admin_state[admin_id]
        state = state_info.get("state")
        
        athlete_service: AthleteService = message.bot.dispatcher["athlete_service"]
        workout_service: WorkoutService = message.bot.dispatcher["workout_service"]
        
        if state == "waiting_athlete_id":
            try:
                telegram_id = int(message.text.strip())
            except ValueError:
                await message.answer("❌ Введите корректный числовой ID.")
                return
            
            state_info["state"] = "waiting_days"
            state_info["data"]["telegram_id"] = telegram_id
            await message.answer(
                "Введи количество дней подписки",
                reply_markup=admin_back_to_athletes_keyboard(),
            )
        
        elif state == "waiting_days":
            try:
                days = int(message.text.strip())
            except ValueError:
                await message.answer("❌ Введите корректное число дней.")
                return
            
            if days <= 0:
                await message.answer("❌ Дней должно быть больше 0.")
                return
            
            telegram_id = state_info["data"]["telegram_id"]
            
            # Check for duplicate
            existing = athlete_service.get_athlete(telegram_id)
            if existing and existing.active and existing.is_subscription_valid():
                _admin_state.pop(admin_id, None)
                await message.answer(f"⚠️ Спортсмен {telegram_id} уже активен.", reply_markup=admin_athletes_menu_keyboard())
                return
            
            # Add athlete
            athlete = athlete_service.add_athlete(
                telegram_id=telegram_id,
                username=f"user_{telegram_id}",
                coach_id=config.ADMIN_ID,
                days=days,
            )
            
            _admin_state.pop(admin_id, None)
            
            await message.answer(
                f"✅ Спортсмен добавлен\n\n"
                f"👤 ID: {athlete.telegram_id}\n"
                f"📅 Подписка: {days} дней\n"
                f"⏳ До: {athlete.subscription_expires_at.strftime('%Y-%m-%d')}",
                reply_markup=admin_athlete_success_keyboard(athlete.telegram_id),
            )
            logger.info(f"Athlete added via admin UI: ID={telegram_id}, days={days}")
        
        elif state == "waiting_find_query":
            try:
                telegram_id = int(message.text.strip())
            except ValueError:
                await message.answer("❌ Введите корректный числовой ID.")
                return
            
            athlete = athlete_service.get_athlete(telegram_id)
            _admin_state.pop(admin_id, None)
            
            if not athlete:
                await message.answer(
                    f"❌ Спортсмен {telegram_id} не найден.",
                    reply_markup=admin_athletes_menu_keyboard(),
                )
                return
            
            status = "🟢 Активен" if athlete.active and athlete.is_subscription_valid() else "🔴 Неактивен"
            days = athlete.days_remaining()
            expires = athlete.subscription_expires_at.strftime("%Y-%m-%d") if athlete.subscription_expires_at else "N/A"
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏋️ Тренировка", callback_data=f"admin_athlete_workout_{telegram_id}")],
                [InlineKeyboardButton(text="⏸ Заморозить", callback_data=f"admin_athlete_freeze_{telegram_id}")],
                [InlineKeyboardButton(text="❌ Удалить", callback_data=f"admin_athlete_remove_{telegram_id}")],
                [InlineKeyboardButton(text="⬅️ В меню спортсменов", callback_data="admin_back_athletes")],
            ])
            
            await message.answer(
                f"🔍 Спортсмен найден\n\n"
                f"👤 ID: {telegram_id}\n"
                f"Статус: {status}\n"
                f"Дней осталось: {days}\n"
                f"Истекает: {expires}",
                reply_markup=keyboard,
            )

    # Register help request handler in workout service callbacks
    original_notify_help = workout_service.notify_help_request
    
    def enhanced_notify_help(athlete_id: int, athlete_username: str, session, exercise):
        """Enhanced help notification that also stores in-memory request."""
        global _help_request_counter
        _help_request_counter += 1
        
        from datetime import datetime
        _help_requests[_help_request_counter] = {
            "athlete_id": athlete_id,
            "athlete_username": athlete_username,
            "exercise": exercise.title,
            "time": datetime.now().strftime("%H:%M"),
        }
        
        return original_notify_help(athlete_id, athlete_username, session, exercise)
    
    workout_service.notify_help_request = enhanced_notify_help

    logger.info("[ADMIN] Admin inline handlers registered")
