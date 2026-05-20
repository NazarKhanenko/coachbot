"""
Business logic services for the coaching platform.

Services encapsulate business rules and coordinate between handlers and storage.
"""

import logging
from typing import Optional

from coachbot.models.entities import Athlete, Coach, ExerciseSession, ExerciseStatus, Workout
from coachbot.storage import get_storage

logger = logging.getLogger(__name__)


class CoachService:
    """Service for coach-related operations."""

    def __init__(self) -> None:
        self.storage = get_storage()

    def register_coach(self, telegram_id: int, username: str) -> Coach:
        """Register a new coach or return existing one."""
        existing = self.storage.get_coach(telegram_id)
        if existing:
            return existing

        coach = Coach(telegram_id=telegram_id, username=username)
        self.storage.add_coach(coach)
        logger.info(f"Registered new coach: {username} (ID: {telegram_id})")
        return coach

    def add_athlete(self, coach_id: int, athlete_telegram_id: int, username: str) -> Athlete:
        """Add an athlete to a coach's roster."""
        coach = self.storage.get_coach(coach_id)
        if not coach:
            raise ValueError(f"Coach with ID {coach_id} not found")

        athlete = Athlete(telegram_id=athlete_telegram_id, username=username, coach_id=coach_id)
        self.storage.add_athlete(athlete)
        logger.info(f"Added athlete {username} to coach {coach.username}")
        return athlete

    def get_my_athletes(self, coach_id: int) -> list[Athlete]:
        """Get all athletes for a coach."""
        return self.storage.get_athletes_by_coach(coach_id)


class WorkoutService:
    """Service for workout-related operations."""

    def __init__(self) -> None:
        self.storage = get_storage()

    def create_workout(self, athlete_id: int, title: str) -> Workout:
        """Create a new workout for an athlete."""
        athlete = self.storage.get_athlete(athlete_id)
        if not athlete:
            raise ValueError(f"Athlete with ID {athlete_id} not found")

        workout_id = f"workout_{athlete_id}_{len(self.storage.get_workouts_for_athlete(athlete_id)) + 1}"
        workout = Workout(id=workout_id, athlete_id=athlete_id, title=title)
        self.storage.add_workout(workout)
        logger.info(f"Created workout '{title}' for athlete {athlete.username}")
        return workout

    def add_block_to_workout(self, workout_id: str, block_name: str) -> None:
        """Add a block to an existing workout."""
        workout = self.storage.get_workout(workout_id)
        if not workout:
            raise ValueError(f"Workout {workout_id} not found")

        from models.entities import Block

        block_id = f"{workout_id}_block_{len(workout.blocks)}"
        block = Block(id=block_id, name=block_name)
        workout.blocks.append(block)
        logger.info(f"Added block '{block_name}' to workout {workout_id}")

    def get_active_workouts(self, athlete_id: int) -> list[Workout]:
        """Get active workouts for an athlete."""
        workouts = self.storage.get_workouts_for_athlete(athlete_id)
        return [w for w in workouts if w.status == "active"]


class ExerciseService:
    """Service for exercise session operations."""

    def __init__(self) -> None:
        self.storage = get_storage()

    def mark_exercise_done(self, workout_id: str, exercise_id: str, athlete_id: int) -> ExerciseSession:
        """Mark an exercise as completed."""
        session = self._get_or_create_session(workout_id, exercise_id, athlete_id)
        session.status = ExerciseStatus.DONE
        session.completed_at = __import__("datetime").datetime.utcnow()
        self.storage.upsert_session(session)
        logger.info(f"Athlete {athlete_id} marked exercise {exercise_id} as done")
        return session

    def request_help(self, workout_id: str, exercise_id: str, athlete_id: int, message: str) -> ExerciseSession:
        """Request help for an exercise."""
        session = self._get_or_create_session(workout_id, exercise_id, athlete_id)
        session.status = ExerciseStatus.NEEDS_HELP
        session.help_request = message
        self.storage.upsert_session(session)
        logger.info(f"Athlete {athlete_id} requested help for exercise {exercise_id}")
        return session

    def _get_or_create_session(self, workout_id: str, exercise_id: str, athlete_id: int) -> ExerciseSession:
        """Get existing session or create a new one."""
        session = self.storage.get_session(workout_id, exercise_id)
        if session:
            return session

        session = ExerciseSession(
            workout_id=workout_id,
            exercise_id=exercise_id,
            athlete_id=athlete_id,
        )
        self.storage.upsert_session(session)
        return session
