"""
Handler routers for the bot.

- message_handlers: Text messages and commands
- callback_handlers: Inline button callbacks
- admin_handlers: Admin-only commands
"""

from aiogram import Dispatcher

from services.athlete_service import AthleteService
from handlers.admin_handlers import admin_router, setup_admin_handlers
from handlers.callback_handlers import callback_router
from handlers.message_handlers import message_router, setup_message_handlers


def setup_handlers(dp: Dispatcher, athlete_service: AthleteService) -> None:
    """Register all routers with the dispatcher."""
    # Message handlers (includes /start with access control)
    setup_message_handlers(dp, athlete_service)
    dp.include_router(message_router)
    
    # Admin handlers (athlete management commands)
    setup_admin_handlers(dp, athlete_service)
    dp.include_router(admin_router)
    
    # Callback handlers (inline buttons)
    dp.include_router(callback_router)


__all__ = [
    "setup_handlers",
]
