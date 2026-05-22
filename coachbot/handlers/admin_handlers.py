"""Admin-only command handlers for athlete management."""
import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import config
from services.athlete_service import AthleteService
from services.workout_service import WorkoutService

logger = logging.getLogger(__name__)

admin_router = Router()


def setup_admin_handlers(dp: Router, athlete_service: AthleteService, workout_service: WorkoutService):
    """Register admin handlers with the router."""
    logger.info("[ADMIN] Setting up admin handlers")

    @admin_router.message(Command("create_demo_workout"))
    async def cmd_create_demo_workout(message: Message):
        """Create a demo workout for an athlete: /create_demo_workout USER_ID"""
        logger.info(f"[TRACE] Handler entered: cmd_create_demo_workout from user {message.from_user.id}")
        
        if message.from_user.id != config.ADMIN_ID:
            logger.info(f"[TRACE] AdminFilter failed: user {message.from_user.id} != {config.ADMIN_ID}")
            await message.answer("⛔ Команда только для администратора.")
            return

        args = message.text.split()
        if len(args) != 2:
            logger.info(f"Invalid admin command usage: /create_demo_workout by {message.from_user.id}")
            await message.answer(
                "❌ Использование: /create_demo_workout USER_ID\n"
                "Пример: /create_demo_workout 123456789"
            )
            return

        # Validate USER_ID is integer
        try:
            user_id = int(args[1])
        except ValueError:
            await message.answer("❌ USER_ID должен быть целым числом.")
            return

        # Check if athlete exists
        athlete = athlete_service.get_athlete(user_id)
        if not athlete:
            await message.answer(f"❌ Спортсмен {user_id} не найден.")
            return

        # Check if athlete is active
        if not athlete.active:
            await message.answer(f"❌ Спортсмен {user_id} не активен.")
            return

        if not athlete.is_subscription_valid():
            await message.answer(f"❌ У спортсмена {user_id} истёк срок подписки.")
            return

        # Create demo workout
        session = workout_service.create_demo_workout(athlete_id=user_id)

        logger.info(f"Demo workout created for athlete {user_id} by admin {message.from_user.id}")

        await message.answer(
            f"✅ Тренировка создана\n\n"
            f"👤 Спортсмен: {user_id}\n"
            f"📋 Название: {session.title}\n"
            f"🏋️ Упражнений: {len(session.exercises)}\n\n"
            f"Спортсмен может начать с /workout"
        )
        logger.info(f"[TRACE] Handler completed: cmd_create_demo_workout")

    @admin_router.message(Command("add_athlete"))
    async def cmd_add_athlete(message: Message):
        """Add a new athlete: /add_athlete USER_ID DAYS"""
        logger.info(f"[TRACE] Handler entered: cmd_add_athlete from user {message.from_user.id}, text: {message.text}")
        
        if message.from_user.id != config.ADMIN_ID:
            logger.info(f"[TRACE] AdminFilter failed: user {message.from_user.id} != {config.ADMIN_ID}")
            await message.answer("⛔ Команда только для администратора.")
            return

        args = message.text.split()
        if len(args) != 3:
            logger.info(f"Invalid admin command usage: /add_athlete by {message.from_user.id}")
            await message.answer(
                "❌ Использование: /add_athlete USER_ID DAYS\n"
                "Пример: /add_athlete 123456789 30"
            )
            return

        # Validate USER_ID is integer
        try:
            user_id = int(args[1])
        except ValueError:
            await message.answer("❌ USER_ID должен быть целым числом.")
            return

        # Validate DAYS is positive integer
        try:
            days = int(args[2])
        except ValueError:
            await message.answer("❌ DAYS должен быть целым числом.")
            return

        if days <= 0:
            await message.answer("❌ DAYS должен быть положительным числом (> 0).")
            return

        # Check for duplicate active athlete
        existing = athlete_service.get_athlete(user_id)
        if existing and existing.active and existing.is_subscription_valid():
            await message.answer("⚠️ Спортсмен уже активен.")
            return

        athlete = athlete_service.add_athlete(
            telegram_id=user_id,
            username=f"user_{user_id}",
            coach_id=config.ADMIN_ID,
            days=days,
        )

        logger.info(f"Athlete added: ID={user_id}, days={days} by admin {message.from_user.id}")

        await message.answer(
            f"✅ Спортсмен добавлен\n\n"
            f"👤 ID: {athlete.telegram_id}\n"
            f"📅 Подписка: {days} дней\n"
            f"⏳ До: {athlete.subscription_expires_at.strftime('%Y-%m-%d')}"
        )
        logger.info(f"[TRACE] Handler completed: cmd_add_athlete")

    @admin_router.message(Command("remove_athlete"))
    async def cmd_remove_athlete(message: Message):
        """Remove an athlete: /remove_athlete USER_ID"""
        logger.info(f"[TRACE] Handler entered: cmd_remove_athlete from user {message.from_user.id}")
        
        if message.from_user.id != config.ADMIN_ID:
            logger.info(f"[TRACE] AdminFilter failed: user {message.from_user.id} != {config.ADMIN_ID}")
            await message.answer("⛔ Команда только для администратора.")
            return

        args = message.text.split()
        if len(args) != 2:
            logger.info(f"Invalid admin command usage: /remove_athlete by {message.from_user.id}")
            await message.answer(
                "❌ Использование: /remove_athlete USER_ID\n"
                "Пример: /remove_athlete 123456789"
            )
            return

        # Validate USER_ID is integer
        try:
            user_id = int(args[1])
        except ValueError:
            await message.answer("❌ USER_ID должен быть целым числом.")
            return

        if athlete_service.remove_athlete(user_id):
            logger.info(f"Athlete removed: ID={user_id} by admin {message.from_user.id}")
            await message.answer(f"⛔ Доступ спортсмена отключён (ID: {user_id}).")
        else:
            await message.answer(f"❌ Спортсмен {user_id} не найден.")
        logger.info(f"[TRACE] Handler completed: cmd_remove_athlete")

    @admin_router.message(Command("list_athletes"))
    async def cmd_list_athletes(message: Message):
        """List all athletes with their status."""
        logger.info(f"[TRACE] Handler entered: cmd_list_athletes from user {message.from_user.id}")
        
        if message.from_user.id != config.ADMIN_ID:
            logger.info(f"[TRACE] AdminFilter failed: user {message.from_user.id} != {config.ADMIN_ID}")
            await message.answer("⛔ Команда только для администратора.")
            return

        athletes = athlete_service.list_athletes()

        if not athletes:
            await message.answer("📭 Спортсменов пока нет.")
            return

        lines = ["📋 **Спортсмены:**", ""]
        for athlete in athletes:
            status = "🟢 Активен" if athlete.active else "🔴 Неактивен"
            days = athlete.days_remaining()
            
            if athlete.subscription_expires_at:
                expires = athlete.subscription_expires_at.strftime("%Y-%m-%d")
            else:
                expires = "N/A"

            lines.append(
                f"• ID: `{athlete.telegram_id}`\n"
                f"  Статус: {status}\n"
                f"  Дней осталось: {days}\n"
                f"  Истекает: {expires}\n"
            )

        await message.answer("\n".join(lines), parse_mode="Markdown")
        logger.info(f"[TRACE] Handler completed: cmd_list_athletes")
    
    logger.info(f"[ADMIN] Admin handlers registered: create_demo_workout, add_athlete, remove_athlete, list_athletes")
