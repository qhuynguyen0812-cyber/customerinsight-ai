"""TV3 Phase 1 domain, state, UI, and canonical regression tests."""

from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import silhouette_score

from src.clustering import (
    analyze_candidate_k,
    get_default_solver_kwargs,
    recommend_k,
    run_kmeans,
)
from src.preprocessing import run_pipeline_preprocessing
from src.state import (
    new_app_state,
    set_clustering_result,
    set_k_analysis,
    set_preprocessed_data,
    set_raw_dataset,
    set_results,
    set_selected_k,
)
from src.validation import load_sample_dataset

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def obvious_clusters() -> np.ndarray:
    rng = np.random.default_rng(42)
    return np.vstack(
        [rng.normal(center, 0.1, (50, 3)) for center in (0.0, 5.0, 10.0)]
    )


def canonical_pipeline():
    validated = load_sample_dataset(ROOT / "data" / "sample_customers.csv")
    processed = run_pipeline_preprocessing(validated.raw_df)
    return validated, processed


def test_solver_defaults_exactly_match_contract() -> None:
    assert get_default_solver_kwargs() == {
        "init": "k-means++",
        "n_init": 10,
        "random_state": 42,
        "max_iter": 300,
        "tol": 0.0001,
    }


def test_analyze_structure_and_computed_recommendation(obvious_clusters) -> None:
    metrics = analyze_candidate_k(obvious_clusters, 2, 4)
    assert metrics["k"] == [2, 3, 4]
    assert len(metrics["inertia"]) == len(metrics["silhouette"]) == 3
    assert all(value > 0 for value in metrics["inertia"])
    assert recommend_k(metrics) == 3


def test_recommendation_uses_max_silhouette_and_smaller_k_tie_break() -> None:
    assert recommend_k({"k": [4, 2, 3], "silhouette": [0.8, 0.8, 0.7]}) == 2


@pytest.mark.parametrize(
    ("k_min", "k_max", "message"),
    [(1, 3, "at least 2"), (4, 3, "greater than or equal")],
)
def test_invalid_analysis_ranges_fail(obvious_clusters, k_min, k_max, message) -> None:
    with pytest.raises(ValueError, match=message):
        analyze_candidate_k(obvious_clusters, k_min, k_max)


def test_analysis_rejects_k_at_sample_count() -> None:
    with pytest.raises(ValueError, match="silhouette is undefined"):
        analyze_candidate_k(np.zeros((4, 3)), 2, 4)


@pytest.mark.parametrize("k", [0, 1])
def test_run_kmeans_rejects_k_below_two(obvious_clusters, k) -> None:
    with pytest.raises(ValueError, match="at least 2"):
        run_kmeans(obvious_clusters, k)


def test_run_kmeans_rejects_k_above_sample_count() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        run_kmeans(np.zeros((3, 2)), 4)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_run_kmeans_rejects_nonfinite_input(bad) -> None:
    matrix = np.zeros((4, 3))
    matrix[0, 0] = bad
    with pytest.raises(ValueError, match="finite"):
        run_kmeans(matrix, 2)


def test_run_kmeans_returns_complete_deterministic_contract(obvious_clusters) -> None:
    first = run_kmeans(obvious_clusters, 3)
    second = run_kmeans(obvious_clusters, 3)
    assert len(first.labels) == len(obvious_clusters)
    np.testing.assert_array_equal(first.labels, second.labels)
    assert first.inertia == second.inertia
    assert first.iterations == second.iterations
    assert first.model.n_iter_ == first.iterations


def test_solver_overrides_are_effective_and_unknown_settings_fail(obvious_clusters) -> None:
    fit = run_kmeans(obvious_clusters, 3, {"max_iter": 20, "tol": 1e-3})
    assert fit.model.max_iter == 20
    assert fit.model.tol == 1e-3
    with pytest.raises(ValueError, match="Unsupported solver"):
        run_kmeans(obvious_clusters, 3, {"algorithm": "lloyd"})


def test_canonical_tv1_tv2_tv3_regression() -> None:
    validated, processed = canonical_pipeline()
    matrix = processed["scaled_matrix"]
    metrics = analyze_candidate_k(matrix, 2, 10)
    recommended = recommend_k(metrics)
    fit = run_kmeans(matrix, 3)

    assert len(validated.raw_df) == 720
    assert len(processed["processed_df"]) == 720
    assert matrix.shape == (720, 3)
    assert recommended == 3
    # Strict deterministic tolerances detect changes to preprocessing or solver defaults.
    assert fit.inertia == pytest.approx(611.4205381920901, rel=1e-12, abs=1e-12)
    assert silhouette_score(matrix, fit.labels) == pytest.approx(
        0.45877917738169266, rel=1e-12, abs=1e-12
    )
    assert fit.iterations == 9


def test_k_analysis_commit_and_selected_k_invalidation() -> None:
    validated, processed = canonical_pipeline()
    state = new_app_state()
    set_raw_dataset(state, validated.raw_df, validated.dataset_signature)
    set_preprocessed_data(
        state,
        processed["processed_df"],
        processed["scaled_matrix"],
        processed["preprocessing_signature"],
    )
    metrics = analyze_candidate_k(state.scaled_matrix, 2, 4)
    set_k_analysis(state, metrics, recommend_k(metrics))
    set_selected_k(state, 3)
    set_clustering_result(
        state, "model", np.zeros(720), "profiles", run_metadata={"run": "current"}
    )
    set_results(state, "results", "export")

    set_selected_k(state, 2)
    assert state.k_metrics is metrics
    assert state.recommended_k == 3
    assert state.selected_k == 2
    assert state.model is state.labels is state.cluster_profiles is None
    assert state.results is state.export_payload is None


def test_analysis_failure_leaves_old_state_untouched() -> None:
    validated, processed = canonical_pipeline()
    state = new_app_state()
    set_raw_dataset(state, validated.raw_df, validated.dataset_signature)
    set_preprocessed_data(
        state, processed["processed_df"], processed["scaled_matrix"], "prep"
    )
    old_metrics = {"k": [2], "inertia": [1.0], "silhouette": [0.2]}
    set_k_analysis(state, old_metrics, 2)
    with pytest.raises(ValueError):
        metrics = analyze_candidate_k(state.scaled_matrix, 1, 4)
        set_k_analysis(state, metrics, recommend_k(metrics))
    assert state.k_metrics is old_metrics
    assert state.recommended_k == 2
