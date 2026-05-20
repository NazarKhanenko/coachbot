"""
In-memory storage for development and testing.

This module provides a simple dictionary-based storage layer.
Will be replaced with a real database in production.
"""

from typing import Optional

from coachbot.models.entities import Athlete, Coach, ExerciseSession, Workout


class InMemoryStorage:
    """Simple in-memory data store."""

    def __init__(self) -> None:
        self.coaches: dict[int, Coach] = {}
        self.athletes: dict[int, Athlete] = {}
        self.workouts: dict[str, Workout] = {}
        self.sessions: dict[tuple[str, str], ExerciseSession] = {}  # (workout_id, exercise_id) -> session

    # Coach operations
    def add_coach(self, coach: Coach) -> None:
        """Add or update a coach."""
        self.coaches[coach.telegram_id] = coach

    def get_coach(self, telegram_id: int) -> Optional[Coach]:
        """Get a coach by Telegram ID."""
        return self.coaches.get(telegram_id)

    # Athlete operations
    def add_athlete(self, athlete: Athlete) -> None:
        """Add or update an athlete."""
        self.athletes[athlete.telegram_id] = athlete

    def get_athlete(self, telegram_id: int) -> Optional[Athlete]:
        """Get an athlete by Telegram ID."""
        return self.athletes.get(telegram_id)

    def get_athletes_by_coach(self, coach_id: int) -> list[Athlete]:
        """Get all athletes for a coach."""
        return [a for a in self.athletes.values() if a.coach_id == coach_id]

    # Workout operations
    def add_workout(self, workout: Workout) -> None:
        """Add or update a workout."""
        self.workouts[workout.id] = workout

    def get_workout(self, workout_id: str) -> Optional[Workout]:
        """Get a workout by ID."""
        return self.workouts.get(workout_id)

    def get_workouts_for_athlete(self, athlete_id: int) -> list[Workout]:
        """Get all workouts for an athlete."""
        return [w for w in self.workouts.values() if w.athlete_id == athlete_id]

    # Session operations
    def upsert_session(self, session: ExerciseSession) -> None:
        """Add or update an exercise session."""
        key = (session.workout_id, session.exercise_id)
        self.sessions[key] = session

    def get_session(self, workout_id: str, exercise_id: str) -> Optional[ExerciseSession]:
        """Get a session by workout and exercise ID."""
        return self.sessions.get((workout_id, exercise_id))


# Global storage instance (singleton for now)
_storage: Optional[InMemoryStorage] = None


def get_storage() -> InMemoryStorage:
    """Get the global storage instance."""
    global _storage
    if _storage is None:
        _storage = InMemoryStorage()
    return _storage
