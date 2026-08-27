"""Regression tests for the canonical TV5 state and invalidation contract."""

import pytest

from src.state import (
    AppState,
    STATE_DEPENDENCIES,
    STATE_SCHEMA,
    downstream_keys,
    new_app_state,
    set_clustering_result,
    set_k_analysis,
    set_outlier_strategy,
    set_preprocessed_data,
    set_raw_dataset,
    set_results,
    set_selected_k,
    set_solver_preferences,
)


def populated_state() -> AppState:
    state = new_app_state()
    set_raw_dataset(state, "raw", "dataset-a")
    set_preprocessed_data(
        state, "processed", "scaled", "prep-a", "eda", outlier_strategy="iqr_clip"
    )
    set_k_analysis(state, {"scores": [1, 2]}, 3)
    set_selected_k(state, 3)
    set_solver_preferences(state, {"max_iter": 350, "tol": 0.0001})
    set_clustering_result(
        state,
        "model",
        [0, 1],
        "profiles",
        run_metadata={"run": "current"},
        results="results",
    )
    state.export_payload = "export"
    return state


def test_schema_and_dependency_graph_cover_latest_app_state() -> None:
    state = new_app_state()
    assert isinstance(state, AppState)
    assert tuple(state.__dataclass_fields__) == STATE_SCHEMA
    assert "run_metadata" in STATE_SCHEMA
    assert all(getattr(state, key) is None for key in STATE_SCHEMA)
    assert set(STATE_DEPENDENCIES) == set(STATE_SCHEMA)
    assert STATE_DEPENDENCIES["run_metadata"] == ("model",)
    assert STATE_DEPENDENCIES["results"] == ("cluster_profiles", "run_metadata")


def test_downstream_keys_are_transitive_and_deterministic() -> None:
    first = downstream_keys("selected_k")
    assert first == downstream_keys("selected_k")
    assert first == tuple(key for key in STATE_SCHEMA if key in first)
    assert first == (
        "model", "labels", "cluster_profiles", "run_metadata", "results", "export_payload"
    )


@pytest.mark.parametrize("change", ["dataset", "preprocessing"])
def test_upstream_changes_clear_run_metadata_results_and_export(change: str) -> None:
    state = populated_state()
    if change == "dataset":
        set_raw_dataset(state, "raw-b", "dataset-b")
        assert (state.raw_df, state.dataset_signature) == ("raw-b", "dataset-b")
        assert state.processed_df is None
    else:
        set_preprocessed_data(state, "processed-b", "scaled-b", "prep-b")
        assert (state.raw_df, state.dataset_signature) == ("raw", "dataset-a")
        assert state.k_metrics is None
    assert state.run_metadata is None
    assert state.results is None
    assert state.export_payload is None


@pytest.mark.parametrize("change", ["selected_k", "solver"])
def test_model_input_changes_preserve_upstream_and_clear_all_outputs(change: str) -> None:
    state = populated_state()
    if change == "selected_k":
        set_selected_k(state, 4)
        assert state.selected_k == 4
        assert state.solver_preferences == {"max_iter": 350, "tol": 0.0001}
    else:
        set_solver_preferences(state, {"max_iter": 400, "tol": 0.0001})
        assert state.selected_k == 3
        assert state.solver_preferences == {"max_iter": 400, "tol": 0.0001}
    assert state.k_metrics == {"scores": [1, 2]}
    for key in ("model", "labels", "cluster_profiles", "run_metadata", "results", "export_payload"):
        assert getattr(state, key) is None


def test_clustering_commit_replaces_all_outputs_and_clears_stale_export() -> None:
    state = populated_state()
    set_clustering_result(
        state, "new-model", [1, 0], "new-profiles",
        run_metadata={"run": "new"}, results="new-results",
    )
    assert (state.model, state.labels, state.cluster_profiles) == (
        "new-model", [1, 0], "new-profiles"
    )
    assert state.run_metadata == {"run": "new"}
    assert state.results == "new-results"
    assert state.export_payload is None


def test_clustering_results_without_metadata_fail_atomically() -> None:
    state = populated_state()
    snapshot = AppState(**vars(state))
    with pytest.raises(ValueError, match="Run metadata"):
        set_clustering_result(
            state, "new-model", [1, 0], "new-profiles",
            run_metadata=None, results="new-results",
        )
    assert state == snapshot


def test_set_results_requires_complete_clustering_prerequisite() -> None:
    state = new_app_state()
    with pytest.raises(ValueError):
        set_results(state, "results")
    state.model = "model"
    state.cluster_profiles = "profiles"
    with pytest.raises(ValueError, match="run metadata"):
        set_results(state, "results", "export")
    state.run_metadata = {"run": "current"}
    set_results(state, "results", "export")
    assert (state.results, state.export_payload) == ("results", "export")


def test_failed_setters_do_not_partially_mutate_valid_state() -> None:
    state = populated_state()
    snapshot = AppState(**vars(state))
    invalid_calls = [
        lambda: set_raw_dataset(state, None, ""),
        lambda: set_outlier_strategy(state, "invalid"),
        lambda: set_preprocessed_data(state, None, "scaled", "prep"),
        lambda: set_k_analysis(state, None, 3),
        lambda: set_selected_k(state, 1),
        lambda: set_clustering_result(state, None, [0], "profiles"),
        lambda: set_results(state, None),
        lambda: set_solver_preferences(state, {"max_iter": True}),
    ]
    for call in invalid_calls:
        with pytest.raises(ValueError):
            call()
        assert state == snapshot


def test_outlier_strategy_change_is_precise_atomic_and_idempotent() -> None:
    state = populated_state()
    solver = state.solver_preferences
    set_outlier_strategy(state, "iqr_clip")
    assert state.model == "model"

    set_outlier_strategy(state, "keep")
    assert state.outlier_strategy == "keep"
    assert (state.raw_df, state.dataset_signature) == ("raw", "dataset-a")
    assert state.solver_preferences == solver
    for key in (
        "processed_df", "scaled_matrix", "preprocessing_signature", "eda_summary",
        "k_metrics", "recommended_k", "selected_k", "model", "labels",
        "cluster_profiles", "run_metadata", "results", "export_payload",
    ):
        assert getattr(state, key) is None


def test_same_solver_preferences_preserve_outputs_and_invalid_values_are_atomic() -> None:
    state = populated_state()
    snapshot = AppState(**vars(state))
    set_solver_preferences(state, {"max_iter": 350, "tol": 0.0001})
    assert state == snapshot

    for invalid in (
        {"max_iter": True}, {"max_iter": 3.5}, {"max_iter": 0},
        {"tol": True}, {"tol": 0}, {"tol": float("nan")},
        {"tol": float("inf")}, {"foo": 123},
    ):
        with pytest.raises(ValueError):
            set_solver_preferences(state, invalid)
        assert state == snapshot
