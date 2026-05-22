"""Admin-only command handlers for athlete management with inline button UI."""
import logging
from typing import Any, Callable, Dict
from aiogram import F, Router, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from config import config
from services.athlete_service import AthleteService
from services.workout_service import WorkoutService
from keyboards.inline_keyboards import (
    admin_main_keyboard,
    admin_athletes_menu_keyboard,
    admin_back_to_athletes_keyboard,
    admin_back_to_main_keyboard,
    admin_athlete_actions_keyboard,
    admin_athlete_profile_keyboard,
    admin_workout_assign_keyboard,
    admin_help_request_keyboard,
    admin_system_keyboard,
    admin_workouts_keyboard,
    admin_weekly_plan_keyboard,
    admin_back_to_workouts_keyboard,
    admin_athlete_success_keyboard,
    admin_warmup_keyboard,
    admin_exercise_placeholder_keyboard,
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


class ServiceInjectionMiddleware(BaseMiddleware):
    """Inject services into handler_data for aiogram 3 compatibility."""
    
    def __init__(self, athlete_service: AthleteService, workout_service: WorkoutService):
        self.athlete_service = athlete_service
        self.workout_service = workout_service
    
    async def __call__(
        self,
        handler: Callable,
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Inject services into handler_data
        data['athlete_service'] = self.athlete_service
        data['workout_service'] = self.workout_service
        return await handler(event, data)


def setup_admin_handlers(dp: Router, athlete_service: AthleteService, workout_service: WorkoutService):
    """Register admin handlers with the router."""
    logger.info("[ADMIN] Setting up admin handlers with inline UI")

    # Store services in dispatcher workflow_data
    dp["athlete_service"] = athlete_service
    dp["workout_service"] = workout_service
    
    # Register middleware for service injection (aiogram 3 compatible)
    admin_router.message.middleware(
        ServiceInjectionMiddleware(athlete_service, workout_service)
    )
    admin_router.callback_query.middleware(
        ServiceInjectionMiddleware(athlete_service, workout_service)
    )

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
                reply_markup=admin_back_to_main_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "Введи Telegram ID спортсмена\n\n⬅️ /cancel - отмена",
                reply_markup=admin_back_to_main_keyboard(),
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
    async def cb_admin_list_athletes(callback: CallbackQuery, athlete_service: AthleteService):
        """Show list of athletes with compact card-style buttons."""
        await callback.answer()
        
        athletes = athlete_service.list_athletes()
        
        if not athletes:
            try:
                await callback.message.edit_text(
                    "📭 Спортсменов пока нет.",
                    reply_markup=admin_back_to_main_keyboard(),
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    "📭 Спортсменов пока нет.",
                    reply_markup=admin_back_to_main_keyboard(),
                )
            return
        
        # Build compact athlete list - each athlete is a clickable button with username as primary identity
        keyboard_buttons = []
        
        for athlete in athletes:
            status_icon = "🟢" if athlete.active and athlete.is_subscription_valid() else "🔴"
            days = athlete.days_remaining()
            username = getattr(athlete, 'username', None)
            
            # Button text: @username • 29 дн. (ID only shown in profile, not here)
            if username:
                btn_label = f"{status_icon} @{username}"
            else:
                btn_label = f"{status_icon} user_{athlete.telegram_id}"
            
            if days is not None:
                btn_label += f" • {days} дн."
            else:
                btn_label += " • frozen"
            
            # Add action button for this athlete (compact inline button)
            keyboard_buttons.append([InlineKeyboardButton(text=btn_label, callback_data=f"admin_athlete_profile_{athlete.telegram_id}")])
        
        # Add navigation buttons
        keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_athletes")])
        keyboard_buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin_back_main")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        try:
            await callback.message.edit_text("👥 Спортсмены:", reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer("👥 Спортсмены:", reply_markup=keyboard)

    @admin_router.callback_query(lambda c: c.data.startswith("admin_athlete_profile_"))
    async def cb_admin_athlete_profile(callback: CallbackQuery, athlete_service: AthleteService):
        """Show athlete profile page with actions."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_athlete_profile_", ""))
        
        athlete = athlete_service.get_athlete(athlete_id)
        if not athlete:
            try:
                await callback.message.edit_text(
                    f"❌ Спортсмен {athlete_id} не найден.",
                    reply_markup=admin_back_to_main_keyboard(),
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    f"❌ Спортсмен {athlete_id} не найден.",
                    reply_markup=admin_back_to_main_keyboard(),
                )
            return
        
        # Determine status
        is_active = athlete.active and athlete.is_subscription_valid()
        is_frozen = not athlete.active
        days = athlete.days_remaining()
        expires = athlete.subscription_expires_at.strftime("%Y-%m-%d") if athlete.subscription_expires_at else "N/A"
        username = getattr(athlete, 'username', f'user_{athlete_id}')
        
        status_text = "🟢 Активен" if is_active else ("⏸ Заморожен" if is_frozen else "🔴 Неактивен")
        
        text = (
            f"👤 Профиль спортсмена\n\n"
            f"ID: {athlete.telegram_id}\n"
            f"Username: @{username}\n"
            f"Статус: {status_text}\n"
            f"Дней осталось: {days}\n"
            f"Истекает: {expires}"
        )
        
        try:
            await callback.message.edit_text(text, reply_markup=admin_athlete_profile_keyboard(athlete_id, is_frozen))
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=admin_athlete_profile_keyboard(athlete_id, is_frozen))

    @admin_router.callback_query(lambda c: c.data.startswith("admin_athlete_toggle_freeze_"))
    async def cb_admin_athlete_toggle_freeze(callback: CallbackQuery, athlete_service: AthleteService):
        """Toggle freeze/unfreeze state for an athlete."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_athlete_toggle_freeze_", ""))
        
        athlete = athlete_service.get_athlete(athlete_id)
        if not athlete:
            try:
                await callback.message.edit_text(
                    f"❌ Спортсмен {athlete_id} не найден.",
                    reply_markup=admin_back_to_main_keyboard(),
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    f"❌ Спортсмен {athlete_id} не найден.",
                    reply_markup=admin_back_to_main_keyboard(),
                )
            return
        
        # Toggle active state
        athlete.active = not athlete.active
        new_status = "разморожен" if athlete.active else "заморожен"
        
        # Reload athlete to get fresh state
        athlete = athlete_service.get_athlete(athlete_id)
        is_frozen = not athlete.active
        
        text = f"✅ Спортсмен {athlete_id} {new_status}."
        
        try:
            await callback.message.edit_text(text, reply_markup=admin_athlete_profile_keyboard(athlete_id, is_frozen))
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=admin_athlete_profile_keyboard(athlete_id, is_frozen))

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
    async def cb_admin_assign_demo(callback: CallbackQuery, athlete_service: AthleteService, workout_service: WorkoutService):
        """Assign demo workout to athlete with comprehensive runtime logging."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_assign_demo_", ""))
        
        # LOG 1: Callback entered
        logger.info(f"[DEMO_WORKOUT] Callback entered for athlete_id={athlete_id}")
        
        # Check if athlete exists and is active
        athlete = athlete_service.get_athlete(athlete_id)
        
        # LOG 2: Athlete found?
        logger.info(f"[DEMO_WORKOUT] Athlete lookup result: {'FOUND' if athlete else 'NOT_FOUND'}")
        if athlete:
            logger.info(f"[DEMO_WORKOUT] Athlete details: telegram_id={athlete.telegram_id}, username={getattr(athlete, 'username', 'N/A')}, active={athlete.active}, subscription_valid={athlete.is_subscription_valid()}")
        
        if not athlete:
            logger.error(f"[DEMO_WORKOUT] Athlete {athlete_id} not found")
            try:
                await callback.message.edit_text(f"❌ Спортсмен {athlete_id} не найден.", reply_markup=admin_back_to_main_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(f"❌ Спортсмен {athlete_id} не найден.", reply_markup=admin_back_to_main_keyboard())
            return
        
        if not athlete.active or not athlete.is_subscription_valid():
            logger.warning(f"[DEMO_WORKOUT] Athlete {athlete_id} is not active or subscription invalid: active={athlete.active}, subscription_valid={athlete.is_subscription_valid()}")
            try:
                await callback.message.edit_text(f"❌ Спортсмен {athlete_id} не активен.", reply_markup=admin_back_to_main_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(f"❌ Спортсмен {athlete_id} не активен.", reply_markup=admin_back_to_main_keyboard())
            return
        
        # LOG 3: Workout service available?
        logger.info(f"[DEMO_WORKOUT] Workout service available: {workout_service is not None}")
        
        # Create demo workout
        session = None
        try:
            session = workout_service.create_demo_workout(athlete_id=athlete_id)
            # LOG 4: Demo workout created?
            logger.info(f"[DEMO_WORKOUT] Demo workout created: session_id={session.session_id if session else 'NONE'}, title={session.title if session else 'N/A'}")
        except Exception as e:
            # LOG 5: Exception traceback
            logger.exception(f"[DEMO_WORKOUT] Exception during workout creation: {type(e).__name__}: {e}")
            try:
                await callback.message.edit_text(f"❌ Ошибка создания тренировки: {e}", reply_markup=admin_back_to_main_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(f"❌ Ошибка создания тренировки: {e}", reply_markup=admin_back_to_main_keyboard())
            return
        
        try:
            await callback.message.edit_text(
                f"✅ Тренировка выдана спортсмену {athlete_id}\n\n"
                f"👤 @{getattr(athlete, 'username', f'user_{athlete_id}')}\n"
                f"🏋️ {session.title}",
                reply_markup=admin_back_to_main_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"✅ Тренировка выдана спортсмену {athlete_id}\n\n"
                f"👤 @{getattr(athlete, 'username', f'user_{athlete_id}')}\n"
                f"🏋️ {session.title}",
                reply_markup=admin_back_to_main_keyboard(),
            )
        
        logger.info(f"[DEMO_WORKOUT] Successfully assigned to athlete {athlete_id} by admin")

    @admin_router.callback_query(lambda c: c.data.startswith("admin_athlete_freeze_"))
    async def cb_admin_athlete_freeze(callback: CallbackQuery, athlete_service: AthleteService):
        """Freeze (deactivate) an athlete and refresh UI."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_athlete_freeze_", ""))
        
        athlete = athlete_service.get_athlete(athlete_id)
        if athlete:
            athlete.active = False
        
        # Reload athlete to get fresh state
        athlete = athlete_service.get_athlete(athlete_id)
        is_frozen = not athlete.active if athlete else True
        
        try:
            await callback.message.edit_text(
                f"⏸ Спортсмен {athlete_id} заморожен.",
                reply_markup=admin_athlete_profile_keyboard(athlete_id, is_frozen),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"⏸ Спортсмен {athlete_id} заморожен.",
                reply_markup=admin_athlete_profile_keyboard(athlete_id, is_frozen),
            )

    @admin_router.callback_query(lambda c: c.data.startswith("admin_athlete_remove_"))
    async def cb_admin_athlete_remove(callback: CallbackQuery, athlete_service: AthleteService):
        """Remove (deactivate) an athlete and return to list."""
        await callback.answer()
        athlete_id = int(callback.data.replace("admin_athlete_remove_", ""))
        
        athlete_service.remove_athlete(athlete_id)
        
        # Return to athletes list which will now show updated list
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

    @admin_router.callback_query(F.data == "admin_workout_warmup")
    async def cb_admin_workout_warmup(callback: CallbackQuery):
        """Show warmup exercises placeholder."""
        await callback.answer()
        try:
            await callback.message.edit_text(
                "🔥 Разминка",
                reply_markup=admin_warmup_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "🔥 Разминка",
                reply_markup=admin_warmup_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_ex_placeholder")
    async def cb_admin_ex_placeholder(callback: CallbackQuery):
        """Show exercise placeholder message."""
        await callback.answer()
        try:
            await callback.message.edit_text(
                "🚧 Упражнение в разработке\n\n"
                "Детали упражнения будут добавлены позже.",
                reply_markup=admin_exercise_placeholder_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "🚧 Упражнение в разработке\n\n"
                "Детали упражнения будут добавлены позже.",
                reply_markup=admin_exercise_placeholder_keyboard(),
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
                    reply_markup=admin_back_to_main_keyboard(),
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    "📨 Запросы помощи\n\nНет активных запросов.",
                    reply_markup=admin_back_to_main_keyboard(),
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
                reply_markup=admin_back_to_main_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "✅ Запрос закрыт.",
                reply_markup=admin_back_to_main_keyboard(),
            )

    @admin_router.callback_query(F.data == "admin_system")
    async def cb_admin_system(callback: CallbackQuery, athlete_service: AthleteService, workout_service: WorkoutService):
        """Show system panel with stats."""
        await callback.answer()
        
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
    async def cb_admin_system_refresh(callback: CallbackQuery, athlete_service: AthleteService, workout_service: WorkoutService):
        """Refresh system panel."""
        await callback.answer()
        
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
                reply_markup=admin_back_to_main_keyboard(),
            )
        except TelegramBadRequest:
            await callback.message.answer(
                "Введи Telegram ID для поиска\n\n⬅️ /cancel - отмена",
                reply_markup=admin_back_to_main_keyboard(),
            )

    @admin_router.message(lambda m: m.from_user.id == config.ADMIN_ID and m.text == "/cancel")
    async def cmd_cancel(message: Message):
        """Cancel current admin flow."""
        _admin_state.pop(message.from_user.id, None)
        await message.answer("❌ Отменено.", reply_markup=admin_athletes_menu_keyboard())

    @admin_router.message(lambda m: m.from_user.id == config.ADMIN_ID)
    async def handle_admin_input(message: Message, athlete_service: AthleteService, workout_service: WorkoutService):
        """Handle admin text input for multi-step flows."""
        admin_id = message.from_user.id
        
        if admin_id not in _admin_state:
            return  # Not in a flow
        
        state_info = _admin_state[admin_id]
        state = state_info.get("state")
        
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
                reply_markup=admin_back_to_main_keyboard(),
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
