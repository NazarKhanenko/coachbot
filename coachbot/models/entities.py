"""
Domain models for the coaching platform.

These are pure data classes representing business entities.
Not tied to any database yet.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ExerciseStatus(Enum):
    """Status of an exercise in a workout."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    NEEDS_HELP = "needs_help"


@dataclass
class Coach:
    """Represents a coach."""

    telegram_id: int
    username: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Athlete:
    """Represents an athlete."""

    telegram_id: int
    username: str
    coach_id: int  # Reference to coach's telegram_id
    active: bool = True
    subscription_expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_subscription_valid(self) -> bool:
        """Check if subscription is currently active."""
        if not self.active or not self.subscription_expires_at:
            return False
        return datetime.utcnow() < self.subscription_expires_at

    def days_remaining(self) -> int:
        """Calculate remaining days of subscription."""
        if not self.subscription_expires_at:
            return 0
        delta = self.subscription_expires_at - datetime.utcnow()
        return max(0, delta.days)


@dataclass
class Exercise:
    """Represents a single exercise within a block."""

    id: str
    name: str
    description: str
    sets: Optional[int] = None
    reps: Optional[str] = None
    duration: Optional[str] = None  # e.g., "30s", "1min"
    video_url: Optional[str] = None


@dataclass
class Block:
    """Represents a block of exercises (e.g., Warm-up, Main Workout)."""

    id: str
    name: str
    exercises: list[Exercise] = field(default_factory=list)


@dataclass
class Workout:
    """Represents a workout assigned to an athlete."""

    id: str
    athlete_id: int  # Reference to athlete's telegram_id
    title: str
    blocks: list[Block] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"  # active, completed, archived


@dataclass
class ExerciseSession:
    """Tracks an athlete's progress on a specific exercise."""

    workout_id: str
    exercise_id: str
    athlete_id: int
    status: ExerciseStatus = ExerciseStatus.PENDING
    help_request: Optional[str] = None
    video_uploaded: bool = False
    completed_at: Optional[datetime] = None
