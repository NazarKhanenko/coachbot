"""
Handler routers for the bot.

- message_handlers: Text messages and commands
- callback_handlers: Inline button callbacks
- admin_handlers: Admin-only commands
"""

from aiogram import Dispatcher

from services.athlete_service import AthleteService
from services.workout_service import WorkoutService
from storage.workout_storage import WorkoutStorage
from handlers.admin_handlers import admin_router, setup_admin_handlers
from handlers.callback_handlers import callback_router, setup_callback_handlers
from handlers.message_handlers import message_router, setup_message_handlers


def setup_handlers(dp: Dispatcher, athlete_service: AthleteService) -> None:
    """Register all routers with the dispatcher."""
    # Initialize workout service
    workout_storage = WorkoutStorage()
    workout_service = WorkoutService(storage=workout_storage)
    
    # Message handlers (includes /start with access control)
    setup_message_handlers(dp, athlete_service, workout_service)
    dp.include_router(message_router)
    
    # Admin handlers (athlete management commands)
    setup_admin_handlers(dp, athlete_service, workout_service)
    dp.include_router(admin_router)
    
    # Callback handlers (inline buttons)
    setup_callback_handlers(dp, workout_service)
    dp.include_router(callback_router)


__all__ = [
    "setup_handlers",
]
