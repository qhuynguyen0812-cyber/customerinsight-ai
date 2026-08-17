"""Small in-memory browser-session adapter for the FastAPI prototype."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

from src.state import AppState, new_app_state
from src.validation import DataQualityReport


@dataclass
class BrowserSession:
    app_state: AppState
    quality_report: DataQualityReport | None = None


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, BrowserSession] = {}
        self._lock = Lock()

    def get(self, session_id: str | None) -> tuple[str, BrowserSession]:
        with self._lock:
            if session_id and session_id in self._sessions:
                return session_id, self._sessions[session_id]
            new_id = uuid4().hex
            session = BrowserSession(new_app_state())
            self._sessions[new_id] = session
            return new_id, session


session_store = SessionStore()
