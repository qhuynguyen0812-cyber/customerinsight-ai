"""Streamlit session binding for the TV5 state contract."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from src.state import AppState, new_app_state


APP_STATE_KEY = "customerinsight_app_state"


def get_app_state(session_state: MutableMapping[str, Any] | None = None) -> AppState:
    """Get the per-session :class:`AppState`, creating it exactly once.

    Tests and non-UI callers may supply any mutable mapping.  Streamlit is
    imported lazily so this module stays importable in ordinary unit tests.
    """

    if session_state is None:
        import streamlit as st

        session_state = st.session_state
    current = session_state.get(APP_STATE_KEY)
    if current is None:
        current = new_app_state()
        session_state[APP_STATE_KEY] = current
    if not isinstance(current, AppState):
        raise TypeError(f"{APP_STATE_KEY} must contain AppState")
    return current


def reset_app_state(session_state: MutableMapping[str, Any] | None = None) -> AppState:
    """Replace the current session's state with a fresh workflow snapshot."""

    if session_state is None:
        import streamlit as st

        session_state = st.session_state
    state = new_app_state()
    session_state[APP_STATE_KEY] = state
    return state
