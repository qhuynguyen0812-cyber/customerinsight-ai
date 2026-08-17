"""Tests for TV5 workflow, session binding, progress, gates, and feedback."""

import pytest

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
    set_selected_k,
)


def state_at(stage: WorkflowStage):
    state = new_app_state()
    if stage >= WorkflowStage.DATA_READY:
        set_raw_dataset(state, "raw", "signature")
    if stage >= WorkflowStage.PREPROCESSED:
        set_preprocessed_data(state, "processed", "scaled", "preprocessing")
    if stage >= WorkflowStage.K_CONFIRMED:
        set_k_analysis(state, {"k": [2, 3]}, 3)
        set_selected_k(state, 3)
    if stage >= WorkflowStage.CLUSTERED:
        set_clustering_result(
            state, "model", [0], "profiles", run_metadata={"run": "current"},
            results="results" if stage >= WorkflowStage.RESULTS_READY else None,
        )
    return state


@pytest.mark.parametrize("stage", list(WorkflowStage))
def test_all_stages_and_progress_are_derived_from_state(stage: WorkflowStage) -> None:
    state = state_at(stage)
    assert workflow_stage(state) == stage
    assert progress_fraction(state) == int(stage) / int(WorkflowStage.RESULTS_READY)


def test_all_page_gate_rules_and_unknown_destination() -> None:
    expected = {
        WorkflowStage.EMPTY: {"overview", "data"},
        WorkflowStage.DATA_READY: {"overview", "data", "preprocessing"},
        WorkflowStage.PREPROCESSED: {"overview", "data", "preprocessing", "eda", "k_analysis"},
        WorkflowStage.K_CONFIRMED: {
            "overview", "data", "preprocessing", "eda", "k_analysis", "clustering"
        },
        WorkflowStage.CLUSTERED: {
            "overview", "data", "preprocessing", "eda", "k_analysis", "clustering", "results"
        },
        WorkflowStage.RESULTS_READY: {
            "overview", "data", "preprocessing", "eda", "k_analysis", "clustering", "results", "export"
        },
    }
    destinations = {"overview", "data", "preprocessing", "eda", "k_analysis", "clustering", "results", "export"}
    for stage, allowed in expected.items():
        state = state_at(stage)
        assert {name for name in destinations if can_access(state, name).allowed} == allowed
    with pytest.raises(KeyError):
        can_access(new_app_state(), "not-a-page")


def test_current_tv4_results_are_ready_and_invalidation_moves_stage_back() -> None:
    state = state_at(WorkflowStage.RESULTS_READY)
    assert workflow_stage(state) == WorkflowStage.RESULTS_READY
    set_selected_k(state, 2)
    assert workflow_stage(state) == WorkflowStage.K_CONFIRMED
    assert state.results is None


def test_results_without_run_metadata_are_not_results_ready() -> None:
    state = state_at(WorkflowStage.CLUSTERED)
    state.results = "orphaned-results"
    state.run_metadata = None
    assert workflow_stage(state) == WorkflowStage.CLUSTERED


def test_complete_canonical_result_is_results_ready() -> None:
    state = state_at(WorkflowStage.RESULTS_READY)
    assert all(
        value is not None
        for value in (state.model, state.cluster_profiles, state.run_metadata, state.results)
    )
    assert workflow_stage(state) == WorkflowStage.RESULTS_READY


def test_flash_is_consumed_once() -> None:
    session = {}
    set_flash(session, "K = 3 confirmed")
    assert consume_flash(session) == FlashMessage("K = 3 confirmed")
    assert consume_flash(session) is None
