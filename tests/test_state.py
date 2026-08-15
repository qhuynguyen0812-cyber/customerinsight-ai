"""Contract tests for TV5 Step 1 state architecture."""

import pytest

from src.state import (
    AppState,
    STATE_DEPENDENCIES,
    STATE_SCHEMA,
    new_app_state,
    set_clustering_result,
    set_k_analysis,
    set_preprocessed_data,
    set_raw_dataset,
    set_results,
    set_selected_k,
    set_solver_preferences,
)


def test_new_state_is_empty_and_uses_the_declared_schema() -> None:
    state = new_app_state()

    assert isinstance(state, AppState)
    assert tuple(state.__dataclass_fields__) == STATE_SCHEMA
    assert all(getattr(state, key) is None for key in STATE_SCHEMA)


def test_dependency_graph_covers_each_state_key_and_canonical_pipeline() -> None:
    assert set(STATE_DEPENDENCIES) == set(STATE_SCHEMA)
    assert STATE_DEPENDENCIES["processed_df"] == ("raw_df", "dataset_signature")
    assert STATE_DEPENDENCIES["scaled_matrix"] == (
        "processed_df",
        "preprocessing_signature",
    )
    assert STATE_DEPENDENCIES["model"] == (
        "scaled_matrix",
        "selected_k",
        "solver_preferences",
    )
    assert STATE_DEPENDENCIES["export_payload"] == ("results",)


def complete_state() -> AppState:
    state = new_app_state()
    set_raw_dataset(state, "raw", "dataset-a")
    set_preprocessed_data(state, "processed", "scaled", "prep-a", "eda")
    set_k_analysis(state, {"scores": [1, 2]}, 3)
    set_selected_k(state, 3)
    set_solver_preferences(state, {"n_init": 10})
    set_clustering_result(state, "model", [0, 1], "profiles")
    set_results(state, "results", "export")
    return state


def test_replacing_dataset_invalidates_every_derived_artifact() -> None:
    state = complete_state()

    set_raw_dataset(state, "raw-b", "dataset-b")

    assert state.raw_df == "raw-b"
    assert state.dataset_signature == "dataset-b"
    assert state.solver_preferences == {"n_init": 10}
    assert all(getattr(state, key) is None for key in STATE_SCHEMA if key not in {
        "raw_df", "dataset_signature", "solver_preferences"
    })


def test_preprocessing_change_preserves_dataset_but_clears_downstream() -> None:
    state = complete_state()

    set_preprocessed_data(state, "processed-b", "scaled-b", "prep-b")

    assert (state.raw_df, state.dataset_signature) == ("raw", "dataset-a")
    assert (state.processed_df, state.scaled_matrix, state.preprocessing_signature) == (
        "processed-b", "scaled-b", "prep-b"
    )
    assert state.k_metrics is None
    assert state.selected_k is None
    assert state.model is None
    assert state.results is None


def test_selected_k_and_solver_changes_only_clear_model_downstream() -> None:
    state = complete_state()

    set_selected_k(state, 4)

    assert state.k_metrics == {"scores": [1, 2]}
    assert state.selected_k == 4
    assert state.model is None
    assert state.results is None

    set_clustering_result(state, "model-2", [0, 1], "profiles-2")
    set_results(state, "results-2")
    set_solver_preferences(state, {"n_init": 20})

    assert state.solver_preferences == {"n_init": 20}
    assert state.selected_k == 4
    assert state.k_metrics == {"scores": [1, 2]}
    assert state.model is None
    assert state.results is None


def test_commits_are_gated_and_do_not_partially_mutate_state() -> None:
    state = new_app_state()

    with pytest.raises(ValueError):
        set_preprocessed_data(state, "processed", "scaled", "prep")
    with pytest.raises(ValueError):
        set_selected_k(state, 3)
    with pytest.raises(ValueError):
        set_clustering_result(state, "model", [0], "profiles")
    with pytest.raises(ValueError):
        set_results(state, "results")

    assert state == AppState()
