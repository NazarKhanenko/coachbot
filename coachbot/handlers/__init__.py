"""
Handler routers for the bot.

- message_handlers: Text messages and commands
- callback_handlers: Inline button callbacks
"""

from aiogram import Dispatcher

from .callback_handlers import callback_router
from .message_handlers import message_router


def setup_handlers(dp: Dispatcher) -> None:
    """Register all routers with the dispatcher."""
    dp.include_router(message_router)
    dp.include_router(callback_router)


__all__ = [
    "setup_handlers",
    "message_router",
    "callback_router",
]
