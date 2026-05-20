"""In-memory storage for workout sessions (MVP)."""
from typing import Optional

from models.entities import WorkoutSession


class WorkoutStorage:
    """In-memory storage for workout session management.
    
    This is a temporary implementation until a real database is added.
    Provides clean interface for workout session CRUD operations.
    """

    def __init__(self):
        self._sessions: dict[str, WorkoutSession] = {}
        # Map athlete_id to active session_id for quick lookup
        self._athlete_active_sessions: dict[int, str] = {}

    def create_workout(self, session: WorkoutSession) -> WorkoutSession:
        """Create a new workout session."""
        self._sessions[session.session_id] = session
        # Track as active session for this athlete
        if not session.completed:
            self._athlete_active_sessions[session.athlete_id] = session.session_id
        return session

    def get_session(self, session_id: str) -> Optional[WorkoutSession]:
        """Get a workout session by ID."""
        return self._sessions.get(session_id)

    def get_active_session_by_athlete(self, athlete_id: int) -> Optional[WorkoutSession]:
        """Get the active workout session for an athlete."""
        session_id = self._athlete_active_sessions.get(athlete_id)
        if session_id:
            session = self._sessions.get(session_id)
            if session and not session.completed:
                return session
        return None

    def update_current_exercise(self, session_id: str, exercise_index: int) -> bool:
        """Update the current exercise index in a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        # Validate index bounds
        if exercise_index < 0 or exercise_index >= len(session.exercises):
            return False
        
        session.current_exercise_index = exercise_index
        return True

    def mark_completed(self, session_id: str) -> bool:
        """Mark a workout session as completed."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.completed = True
        # Remove from active sessions map
        if session.athlete_id in self._athlete_active_sessions:
            del self._athlete_active_sessions[session.athlete_id]
        return True

    def get_all_sessions_for_athlete(self, athlete_id: int) -> list[WorkoutSession]:
        """Get all workout sessions for an athlete (including completed)."""
        return [s for s in self._sessions.values() if s.athlete_id == athlete_id]
