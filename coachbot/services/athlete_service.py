"""Athlete management service.

This service handles all athlete-related business logic.
It acts as a facade between handlers and storage.
"""
from datetime import datetime
from typing import Optional

from ..models.entities import Athlete
from ..storage.athlete_storage import AthleteStorage


class AthleteService:
    """Service for managing athletes."""

    def __init__(self, storage: AthleteStorage):
        self.storage = storage

    def add_athlete(
        self,
        telegram_id: int,
        username: str,
        coach_id: int,
        days: int = 30,
    ) -> Athlete:
        """Add a new athlete with subscription."""
        return self.storage.add_athlete(
            telegram_id=telegram_id,
            username=username,
            coach_id=coach_id,
            days=days,
        )

    def get_athlete(self, telegram_id: int) -> Optional[Athlete]:
        """Get athlete by Telegram ID."""
        return self.storage.get_athlete(telegram_id)

    def remove_athlete(self, telegram_id: int) -> bool:
        """Remove (deactivate) an athlete."""
        return self.storage.remove_athlete(telegram_id)

    def list_athletes(self) -> list[Athlete]:
        """List all athletes."""
        # Check and deactivate expired before listing
        self.storage.check_and_deactivate_expired()
        return self.storage.list_athletes()

    def has_access(self, telegram_id: int) -> bool:
        """Check if user has valid access."""
        athlete = self.storage.get_athlete(telegram_id)
        if not athlete:
            return False
        # Auto-deactivate if expired
        if athlete.active and not athlete.is_subscription_valid():
            athlete.active = False
            return False
        return athlete.active

    def get_access_info(self, telegram_id: int) -> Optional[dict]:
        """Get access information for an athlete."""
        athlete = self.storage.get_athlete(telegram_id)
        if not athlete:
            return None
        
        return {
            "active": athlete.active,
            "valid": athlete.is_subscription_valid(),
            "days_remaining": athlete.days_remaining(),
            "expires_at": athlete.subscription_expires_at,
        }
