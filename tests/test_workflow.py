"""Tests for TV5 workflow, session binding and one-shot feedback."""

import pytest

from components.states import APP_STATE_KEY, get_app_state, reset_app_state
from components.workflow import (
    FlashMessage,
    WorkflowStage,
    can_access,
    consume_flash,
    progress_fraction,
    set_flash,
    workflow_stage,
)
from src.state import (
    new_app_state,
    set_clustering_result,
    set_k_analysis,
    set_preprocessed_data,
    set_raw_dataset,
    set_results,
    set_selected_k,
)


def state_at(stage: WorkflowStage):
    state = new_app_state()
    if stage >= WorkflowStage.DATA_READY:
        set_raw_dataset(state, "raw", "signature")
    if stage >= WorkflowStage.PREPROCESSED:
        set_preprocessed_data(state, "processed", "scaled", "preprocessing")
    if stage >= WorkflowStage.K_CONFIRMED:
        set_k_analysis(state, {"k": 3}, 3)
        set_selected_k(state, 3)
    if stage >= WorkflowStage.CLUSTERED:
        set_clustering_result(state, "model", [0], "profiles")
    if stage >= WorkflowStage.RESULTS_READY:
        set_results(state, "results", "export")
    return state


@pytest.mark.parametrize("stage", list(WorkflowStage))
def test_stage_and_progress_are_derived_from_valid_state(stage: WorkflowStage) -> None:
    state = state_at(stage)
    assert workflow_stage(state) == stage
    assert progress_fraction(state) == stage / WorkflowStage.RESULTS_READY


def test_gating_prevents_navigation_before_prerequisites() -> None:
    state = state_at(WorkflowStage.PREPROCESSED)

    assert can_access(state, "k_analysis").allowed
    denied = can_access(state, "clustering")
    assert not denied.allowed
    assert denied.message == "Analyze and confirm K before running K-Means."
    with pytest.raises(KeyError):
        can_access(state, "not-a-page")


def test_flash_is_consumed_once() -> None:
    session = {}
    set_flash(session, "K = 3 confirmed")

    assert consume_flash(session) == FlashMessage("K = 3 confirmed")
    assert consume_flash(session) is None


def test_state_session_binding_is_stable_and_resettable() -> None:
    session = {}
    first = get_app_state(session)
    assert get_app_state(session) is first
    second = reset_app_state(session)
    assert second is not first
    assert session[APP_STATE_KEY] is second
