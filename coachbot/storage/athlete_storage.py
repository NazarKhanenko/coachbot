"""In-memory storage service for athletes with JSON persistence."""
from datetime import datetime, timedelta
from typing import Optional
import os

from models.entities import Athlete
from storage.json_storage import JSONStorage, datetime_to_str


# Path to athletes JSON file
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
ATHLETES_FILE = os.path.join(DATA_DIR, 'athletes.json')


class AthleteStorage:
    """Hybrid storage for athlete management.
    
    Uses in-memory cache for fast access with JSON persistence.
    Provides clean interface for athlete CRUD operations.
    """

    def __init__(self):
        self._athletes: dict[int, Athlete] = {}
        self._storage = JSONStorage(ATHLETES_FILE)
        self._load_from_disk()
    
    def _load_from_disk(self) -> None:
        """Load athletes from JSON file into memory."""
        data = self._storage.load()
        for telegram_id_str, athlete_data in data.items():
            telegram_id = int(telegram_id_str)
            # Parse datetime fields
            if 'subscription_expires_at' in athlete_data and athlete_data['subscription_expires_at']:
                athlete_data['subscription_expires_at'] = datetime.fromisoformat(athlete_data['subscription_expires_at'])
            elif 'subscription_expires' in athlete_data and athlete_data['subscription_expires']:
                # Backward compatibility: old field name
                athlete_data['subscription_expires_at'] = datetime.fromisoformat(athlete_data['subscription_expires'])
            
            if 'created_at' in athlete_data and athlete_data['created_at']:
                athlete_data['created_at'] = datetime.fromisoformat(athlete_data['created_at'])
            
            # Remove fields that are not part of Athlete dataclass
            athlete_data.pop('frozen', None)
            athlete_data.pop('subscription_days', None)
            athlete_data.pop('subscription_expires', None)
            
            athlete = Athlete(**athlete_data)
            self._athletes[telegram_id] = athlete
    
    def _save_to_disk(self) -> None:
        """Save all athletes to JSON file."""
        data = {}
        for telegram_id, athlete in self._athletes.items():
            athlete_dict = {
                'telegram_id': athlete.telegram_id,
                'username': athlete.username,
                'coach_id': athlete.coach_id,
                'active': athlete.active,
                'frozen': not athlete.active,  # Derived field for clarity
                'subscription_days': 0,  # Will be calculated on load
                'subscription_expires': athlete.subscription_expires_at.isoformat() if athlete.subscription_expires_at else None,
                'created_at': athlete.created_at.isoformat(),
            }
            data[str(telegram_id)] = athlete_dict
        self._storage.save(data)

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
        self._save_to_disk()
        return athlete
    
    def create_lightweight_profile(self, telegram_id: int, username: str) -> Athlete:
        """Create a lightweight athlete profile (auto-registration).
        
        Used when any user presses /start but is not yet registered.
        Profile is inactive until admin activates it.
        """
        athlete = Athlete(
            telegram_id=telegram_id,
            username=username,
            coach_id=0,  # No coach assigned yet
            active=False,  # Inactive until admin activates
            subscription_expires_at=None,
        )
        self._athletes[telegram_id] = athlete
        self._save_to_disk()
        return athlete

    def get_athlete(self, telegram_id: int) -> Optional[Athlete]:
        """Get athlete by Telegram ID."""
        return self._athletes.get(telegram_id)

    def remove_athlete(self, telegram_id: int) -> bool:
        """Remove (deactivate) an athlete."""
        athlete = self._athletes.get(telegram_id)
        if athlete:
            athlete.active = False
            self._save_to_disk()
            return True
        return False
    
    def freeze_athlete(self, telegram_id: int) -> bool:
        """Freeze an athlete (deactivate without removing)."""
        athlete = self._athletes.get(telegram_id)
        if athlete:
            athlete.active = False
            self._save_to_disk()
            return True
        return False
    
    def activate_athlete(self, telegram_id: int, days: int = 30) -> bool:
        """Activate an athlete with subscription."""
        athlete = self._athletes.get(telegram_id)
        if athlete:
            athlete.active = True
            athlete.subscription_expires_at = datetime.utcnow() + timedelta(days=days)
            self._save_to_disk()
            return True
        return False

    def list_athletes(self) -> list[Athlete]:
        """List all athletes."""
        # Check and deactivate expired before listing
        self.check_and_deactivate_expired()
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
        if deactivated:
            self._save_to_disk()
        return deactivated
