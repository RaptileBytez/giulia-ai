import os
import json
from pathlib import Path
from google.genai import types
from utils.logger import Logger

log = Logger("HistoryManager")

class HistoryManager:
    """Handles disk-based persistence of chat history using Pydantic serialization.

    This manager ensures that conversation state survives application restarts 
    by mapping Gemini's internal 'Content' objects to standard JSON.

    Attributes:
        storage_dir (Path): Validated path to the history storage directory.
    """
    def __init__(self, storage_dir="data/chat_history", provider_type="gemini"):
        """Sets up the history storage directory.

        Args:
            storage_dir (str): Relative path for JSON storage. 
                Defaults to "data/chat_history".
            provider_type (str): The type of AI provider (e.g., "gemini", "mock").
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.provider_type = provider_type
    
    def _get_path(self, session_id: str) -> Path:
        """Generates the file path for a given session."""
        return self.storage_dir / f"{session_id}.json"
    
    def load_history(self, session_id: str):
        path = self._get_path(session_id)
        if not path.exists():
            log.info(f"No existing history found for session: {session_id}")
            return []
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                neutral_data = json.load(f)
            
            if self.provider_type == "gemini":
                # WICHTIG: Rückführung des neutralen Formats in Gemini-Struktur
                history = [
                    types.Content(
                        role="model" if msg["role"] == "assistant" else "user",
                        parts=[types.Part(text=msg["content"])]
                    ) for msg in neutral_data
                ]
                log.info(f"Successfully loaded {len(history)} messages for Gemini.")
                return history
            
            elif self.provider_type == "mock":
                log.info(f"Loaded {len(neutral_data)} messages for mock provider.")
                return neutral_data
            
            else:
                log.warning(f"Unknown provider type '{self.provider_type}'. Returning raw data.")
                return neutral_data
                
        except Exception as e:
            log.error(f"Error loading history for session {session_id}: {e}")
            return []

    def save_history(self, session_id: str, history):
        """Serializes the current conversation history to disk.

        Args:
            history (list): A list of types.Content objects to save.
        """
        path = self._get_path(session_id)

        try:
            neutral_history = []
            for msg in history:
                if hasattr(msg, 'model_dump'):
                    dump = msg.model_dump(exclude_none=True)
                    role = "assistant" if dump.get("role") == "model" else dump.get("role", "user")
                    content = dump.get("parts")[0].get("text", "") if dump.get("parts") else ""
                    neutral_history.append({"role": role, "content": content})
                else:
                    neutral_history.append(msg)
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(neutral_history, f, indent=4)

            log.debug(f"History for session {session_id} saved to {path}")
        except Exception as e:
            log.error(f"Error saving history for session {session_id}: {str(e)}")