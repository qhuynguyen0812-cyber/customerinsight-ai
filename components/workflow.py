"""Workflow gating, progress and one-shot feedback for TV5."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from collections.abc import MutableMapping
from typing import Any

from src.state import AppState


class WorkflowStage(IntEnum):
    EMPTY = 0
    DATA_READY = 1
    PREPROCESSED = 2
    K_CONFIRMED = 3
    CLUSTERED = 4
    RESULTS_READY = 5


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    message: str | None = None


@dataclass(frozen=True)
class FlashMessage:
    text: str
    level: str = "success"


FLASH_KEY = "customerinsight_flash"


def workflow_stage(state: AppState) -> WorkflowStage:
    """Calculate the highest valid completed stage from state, never from UI."""

    if state.results is not None:
        return WorkflowStage.RESULTS_READY
    if all(value is not None for value in (state.model, state.labels, state.cluster_profiles)):
        return WorkflowStage.CLUSTERED
    if state.selected_k is not None and state.k_metrics is not None:
        return WorkflowStage.K_CONFIRMED
    if all(value is not None for value in (state.processed_df, state.scaled_matrix, state.preprocessing_signature)):
        return WorkflowStage.PREPROCESSED
    if state.raw_df is not None and state.dataset_signature is not None:
        return WorkflowStage.DATA_READY
    return WorkflowStage.EMPTY


def progress_fraction(state: AppState) -> float:
    """Return Streamlit-friendly progress in the inclusive ``0.0..1.0`` range."""

    return workflow_stage(state) / WorkflowStage.RESULTS_READY


def can_access(state: AppState, destination: str) -> GateResult:
    """Check page/action prerequisites using the canonical names below.

    ``data`` and ``overview`` are always reachable.  Feature pages call this
    before rendering an action and use the returned message in their UI.
    """

    stage = workflow_stage(state)
    requirements = {
        "overview": (WorkflowStage.EMPTY, None),
        "data": (WorkflowStage.EMPTY, None),
        "preprocessing": (WorkflowStage.DATA_READY, "Load or upload a valid dataset first."),
        "eda": (WorkflowStage.PREPROCESSED, "Process the dataset before exploring it."),
        "k_analysis": (WorkflowStage.PREPROCESSED, "Process the dataset before analyzing K."),
        "clustering": (WorkflowStage.K_CONFIRMED, "Analyze and confirm K before running K-Means."),
        "results": (WorkflowStage.CLUSTERED, "Run K-Means before viewing results."),
        "export": (WorkflowStage.RESULTS_READY, "Prepare results before exporting them."),
    }
    try:
        required, message = requirements[destination]
    except KeyError as exc:
        raise KeyError(f"Unknown workflow destination: {destination}") from exc
    return GateResult(stage >= required, None if stage >= required else message)


def set_flash(session_state: MutableMapping[str, Any], text: str, level: str = "success") -> None:
    """Queue a feedback message for exactly one subsequent render."""

    session_state[FLASH_KEY] = FlashMessage(text=text, level=level)


def consume_flash(session_state: MutableMapping[str, Any]) -> FlashMessage | None:
    """Return and remove the queued feedback message, preventing rerun repeats."""

    message = session_state.pop(FLASH_KEY, None)
    if message is None:
        return None
    if not isinstance(message, FlashMessage):
        raise TypeError(f"{FLASH_KEY} must contain FlashMessage")
    return message
