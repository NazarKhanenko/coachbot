"""In-memory storage service for athletes."""
from datetime import datetime, timedelta
from typing import Optional

from coachbot.models.entities import Athlete


class AthleteStorage:
    """In-memory storage for athlete management.
    
    This is a temporary implementation until a real database is added.
    Provides clean interface for athlete CRUD operations.
    """

    def __init__(self):
        self._athletes: dict[int, Athlete] = {}

    def add_athlete(
        self,
        telegram_id: int,
        username: str,
        coach_id: int,
        days: int = 30,
    ) -> Athlete:
        """Add a new athlete with subscription."""
        expires_at = datetime.utcnow() + timedelta(days=days)
        athlete = Athlete(
            telegram_id=telegram_id,
            username=username,
            coach_id=coach_id,
            active=True,
            subscription_expires_at=expires_at,
        )
        self._athletes[telegram_id] = athlete
        return athlete

    def get_athlete(self, telegram_id: int) -> Optional[Athlete]:
        """Get athlete by Telegram ID."""
        return self._athletes.get(telegram_id)

    def remove_athlete(self, telegram_id: int) -> bool:
        """Remove (deactivate) an athlete."""
        athlete = self._athletes.get(telegram_id)
        if athlete:
            athlete.active = False
            return True
        return False

    def list_athletes(self) -> list[Athlete]:
        """List all athletes."""
        return list(self._athletes.values())

    def check_and_deactivate_expired(self) -> list[int]:
        """Check for expired subscriptions and deactivate them.
        
        Returns list of deactivated athlete IDs.
        """
        deactivated = []
        for athlete in self._athletes.values():
            if athlete.active and not athlete.is_subscription_valid():
                athlete.active = False
                deactivated.append(athlete.telegram_id)
        return deactivated
