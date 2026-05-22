"""In-memory storage for workout sessions with JSON persistence."""
import os
from typing import Optional
from datetime import datetime

from models.entities import WorkoutSession, WorkoutExercise
from storage.json_storage import JSONStorage


# Path to workouts JSON file
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
WORKOUTS_FILE = os.path.join(DATA_DIR, 'workouts.json')


class WorkoutStorage:
    """Hybrid storage for workout session management.
    
    Uses in-memory cache for fast access with JSON persistence.
    Provides clean interface for workout session CRUD operations.
    """

    def __init__(self):
        self._sessions: dict[str, WorkoutSession] = {}
        # Map athlete_id to active session_id for quick lookup
        self._athlete_active_sessions: dict[int, str] = {}
        self._storage = JSONStorage(WORKOUTS_FILE)
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load workouts from JSON file into memory."""
        data = self._storage.load()
        for session_id, session_data in data.items():
            # Parse datetime fields
            if 'created_at' in session_data and session_data['created_at']:
                session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
            
            # Reconstruct exercises
            exercises = []
            for ex_data in session_data.get('exercises', []):
                exercise = WorkoutExercise(**ex_data)
                exercises.append(exercise)
            session_data['exercises'] = exercises
            
            session = WorkoutSession(**session_data)
            self._sessions[session_id] = session
            
            # Track active sessions
            if not session.completed:
                self._athlete_active_sessions[session.athlete_id] = session.session_id
    
    def _save_to_disk(self) -> None:
        """Save all workouts to JSON file."""
        data = {}
        for session_id, session in self._sessions.items():
            # Convert exercises to dicts
            exercises_list = []
            for ex in session.exercises:
                ex_dict = {
                    'title': ex.title,
                    'description': ex.description,
                    'sets': ex.sets,
                    'reps': ex.reps,
                    'rest_seconds': ex.rest_seconds,
                    'video_url': ex.video_url,
                    'telegram_file_id': ex.telegram_file_id,
                    'media_type': ex.media_type,
                    'requires_video': ex.requires_video,
                    'state': ex.state,
                }
                exercises_list.append(ex_dict)
            
            session_dict = {
                'session_id': session.session_id,
                'athlete_id': session.athlete_id,
                'title': session.title,
                'exercises': exercises_list,
                'current_exercise_index': session.current_exercise_index,
                'completed': session.completed,
                'created_at': session.created_at.isoformat(),
                'active_message_id': session.active_message_id,
                'active_chat_id': session.active_chat_id,
            }
            data[session_id] = session_dict
        self._storage.save(data)

    def create_workout(self, session: WorkoutSession) -> WorkoutSession:
        """Create a new workout session."""
        self._sessions[session.session_id] = session
        # Track as active session for this athlete
        if not session.completed:
            self._athlete_active_sessions[session.athlete_id] = session.session_id
        self._save_to_disk()
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
        self._save_to_disk()
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
        self._save_to_disk()
        return True

    def get_all_sessions_for_athlete(self, athlete_id: int) -> list[WorkoutSession]:
        """Get all workout sessions for an athlete (including completed)."""
        return [s for s in self._sessions.values() if s.athlete_id == athlete_id]
    
    def update_exercise_state(self, session_id: str, exercise_index: int, state: str) -> bool:
        """Update the state of a specific exercise in a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        if exercise_index < 0 or exercise_index >= len(session.exercises):
            return False
        
        session.exercises[exercise_index].state = state
        self._save_to_disk()
        return True
    
    def set_active_message(self, session_id: str, chat_id: int, message_id: int) -> bool:
        """Store the active workout message reference for editing."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.active_chat_id = chat_id
        session.active_message_id = message_id
        self._save_to_disk()
        return True
