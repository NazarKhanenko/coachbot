"""Workout session service (MVP).

This service handles all workout session business logic.
It acts as a facade between handlers and storage.
"""
import uuid
from typing import Optional

from config import config
from models.entities import WorkoutExercise, WorkoutSession
from storage.workout_storage import WorkoutStorage


class WorkoutService:
    """Service for managing workout sessions."""

    def __init__(self, storage: WorkoutStorage):
        self.storage = storage

    def create_demo_workout(self, athlete_id: int) -> WorkoutSession:
        """Create a demo workout with 3 exercises for an athlete."""
        exercises = [
            WorkoutExercise(
                title="Sprint A-Skips",
                description="Разогрев и активация спринтовой механики.",
                sets=3,
                reps="20 м",
                rest_seconds=45,
                video_url="https://example.com/sprint-a-skips",
                requires_video=False,
            ),
            WorkoutExercise(
                title="Lateral Bounds",
                description="Боковые прыжки с акцентом на контроль и расстояние.",
                sets=3,
                reps="10 на ногу",
                rest_seconds=60,
                video_url="https://example.com/lateral-bounds",
                requires_video=True,
            ),
            WorkoutExercise(
                title="Broad Jumps",
                description="Прыжки в длину с места на максимальную дистанцию.",
                sets=4,
                reps="5 повторений",
                rest_seconds=90,
                video_url=None,
                requires_video=False,
            ),
        ]

        session = WorkoutSession(
            session_id=str(uuid.uuid4()),
            athlete_id=athlete_id,
            title="Demo Speed & Power Session",
            exercises=exercises,
            current_exercise_index=0,
            completed=False,
        )

        return self.storage.create_workout(session)

    def get_current_exercise(self, athlete_id: int) -> Optional[tuple[WorkoutSession, WorkoutExercise, int]]:
        """Get the current exercise for an athlete's active workout.
        
        Returns tuple of (session, exercise, total_exercises) or None if no active workout.
        """
        session = self.storage.get_active_session_by_athlete(athlete_id)
        if not session or session.completed:
            return None

        if session.current_exercise_index >= len(session.exercises):
            return None

        exercise = session.exercises[session.current_exercise_index]
        return (session, exercise, len(session.exercises))

    def get_current_exercise_by_session(self, session_id: str) -> Optional[tuple[WorkoutSession, WorkoutExercise, int]]:
        """Get the current exercise by session ID.
        
        Returns tuple of (session, exercise, total_exercises) or None if not found.
        """
        session = self.storage.get_session(session_id)
        if not session or session.completed:
            return None

        if session.current_exercise_index >= len(session.exercises):
            return None

        exercise = session.exercises[session.current_exercise_index]
        return (session, exercise, len(session.exercises))

    def next_exercise(self, session_id: str) -> Optional[tuple[WorkoutSession, WorkoutExercise, int]]:
        """Move to the next exercise in the session.
        
        Returns tuple of (session, exercise, total_exercises) or None if at end.
        """
        session = self.storage.get_session(session_id)
        if not session or session.completed:
            return None

        next_index = session.current_exercise_index + 1
        if next_index >= len(session.exercises):
            return None

        self.storage.update_current_exercise(session_id, next_index)
        exercise = session.exercises[next_index]
        return (session, exercise, len(session.exercises))

    def previous_exercise(self, session_id: str) -> Optional[tuple[WorkoutSession, WorkoutExercise, int]]:
        """Move to the previous exercise in the session.
        
        Returns tuple of (session, exercise, total_exercises) or None if at start.
        """
        session = self.storage.get_session(session_id)
        if not session or session.completed:
            return None

        prev_index = session.current_exercise_index - 1
        if prev_index < 0:
            return None

        self.storage.update_current_exercise(session_id, prev_index)
        exercise = session.exercises[prev_index]
        return (session, exercise, len(session.exercises))

    def complete_workout(self, session_id: str) -> bool:
        """Mark a workout session as completed."""
        return self.storage.mark_completed(session_id)

    def notify_help_request(self, athlete_id: int, athlete_username: str, 
                            session: WorkoutSession, exercise: WorkoutExercise) -> str:
        """Generate help notification message for admin.
        
        Returns the formatted notification message.
        """
        return (
            f"🆘 Запрос помощи\n\n"
            f"👤 Игрок: @{athlete_username}\n"
            f"🏃 Упражнение: {exercise.title}"
        )
