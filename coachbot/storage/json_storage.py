"""JSON-based persistence layer for athlete and workout data.

Provides atomic read-modify-write operations with UTF-8 encoding.
No database dependencies - pure JSON file storage.
"""
import json
import os
import tempfile
import shutil
from datetime import datetime
from typing import Any, Optional
import threading


class JSONStorage:
    """Thread-safe JSON storage with atomic writes."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Create the JSON file if it doesn't exist."""
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self._write_raw({})
    
    def _read_raw(self) -> dict:
        """Read raw JSON data from file."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _write_raw(self, data: dict) -> None:
        """Atomically write JSON data to file using temp file + rename."""
        dir_path = os.path.dirname(self.filepath)
        
        # Write to temporary file first
        fd, temp_path = tempfile.mkstemp(suffix='.json', dir=dir_path)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            # Atomic rename
            shutil.move(temp_path, self.filepath)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def load(self) -> dict:
        """Load data with thread safety."""
        with self._lock:
            return self._read_raw()
    
    def save(self, data: dict) -> None:
        """Save data with thread safety."""
        with self._lock:
            self._write_raw(data)
    
    def update(self, modifier_func) -> dict:
        """Atomic read-modify-write operation.
        
        Args:
            modifier_func: Function that takes current data and returns modified data
        
        Returns:
            The updated data
        """
        with self._lock:
            data = self._read_raw()
            modified_data = modifier_func(data)
            self._write_raw(modified_data)
            return modified_data


def datetime_to_str(obj: Any) -> Any:
    """JSON encoder helper for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def str_to_datetime(s: str) -> datetime:
    """Convert ISO format string back to datetime."""
    return datetime.fromisoformat(s)
