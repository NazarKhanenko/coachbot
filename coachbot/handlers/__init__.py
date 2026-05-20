"""
Handler routers for the bot.

- message_handlers: Text messages and commands
- callback_handlers: Inline button callbacks
- admin_handlers: Admin-only commands
"""

from aiogram import Dispatcher

from ..services.athlete_service import AthleteService
from .admin_handlers import setup_admin_handlers
from .callback_handlers import callback_router
from .message_handlers import setup_message_handlers


def setup_handlers(dp: Dispatcher, athlete_service: AthleteService) -> None:
    """Register all routers with the dispatcher."""
    # Message handlers (includes /start with access control)
    setup_message_handlers(dp, athlete_service)
    
    # Admin handlers (athlete management commands)
    setup_admin_handlers(dp, athlete_service)
    
    # Callback handlers (inline buttons)
    dp.include_router(callback_router)


__all__ = [
    "setup_handlers",
]
