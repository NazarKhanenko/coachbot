"""
Storage layer for data persistence.

Currently provides in-memory storage for development.
Will support database backends in production.
"""

from .in_memory import InMemoryStorage, get_storage
from .athlete_storage import AthleteStorage

__all__ = [
    "InMemoryStorage",
    "get_storage",
    "AthleteStorage",
]
