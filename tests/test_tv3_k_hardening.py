"""TV3 Phase 2 evidence for K-analysis and K-Means boundary contracts."""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.clustering import (
    KMeansResult,
    analyze_candidate_k,
    get_default_solver_kwargs,
    recommend_k,
    run_kmeans,
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
from web.app import app


@pytest.fixture
def matrix() -> np.ndarray:
    return np.array(
        [
            [0.0, 0.0],
            [0.1, 0.2],
            [5.0, 5.0],
            [5.2, 5.1],
            [10.0, 10.0],
            [10.2, 10.1],
        ]
    )


def test_public_result_contract_and_backward_unpacking(matrix: np.ndarray) -> None:
    fit = run_kmeans(matrix, 3)

    assert isinstance(fit, KMeansResult)
    assert fit.model is not None
    assert len(fit.labels) == len(matrix)
    assert isinstance(fit.inertia, float)
    assert isinstance(fit.iterations, int)
    model, labels = fit
    assert model is fit.model
    assert labels is fit.labels


def test_direct_fit_allows_k_equal_to_sample_count() -> None:
    fit = run_kmeans(np.eye(3), 3)

    assert fit.model.n_clusters == 3
    assert len(np.unique(fit.labels)) == 3


@pytest.mark.parametrize("bad_k", [True, False, 2.5, "3"])
def test_direct_fit_rejects_non_integer_and_bool_k(matrix: np.ndarray, bad_k: object) -> None:
    with pytest.raises(ValueError, match="integer"):
        run_kmeans(matrix, bad_k)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_matrix",
    [
        [1.0, 2.0],
        [],
        np.empty((2, 0)),
        [["not-numeric", "data"], ["still", "invalid"]],
        [[0.0, np.nan], [1.0, 2.0]],
        [[0.0, np.inf], [1.0, 2.0]],
        [[0.0, -np.inf], [1.0, 2.0]],
    ],
)
def test_matrix_validation_rejects_malformed_input(bad_matrix: object) -> None:
    with pytest.raises(ValueError):
        run_kmeans(bad_matrix, 2)  # type: ignore[arg-type]


def test_custom_and_single_candidate_ranges_are_inclusive(matrix: np.ndarray) -> None:
    custom = analyze_candidate_k(matrix, 3, 5)
    single = analyze_candidate_k(matrix, 3, 3)

    assert custom["k"] == [3, 4, 5]
    assert len(custom["inertia"]) == len(custom["silhouette"]) == 3
    assert single["k"] == [3]
    assert len(single["inertia"]) == len(single["silhouette"]) == 1


@pytest.mark.parametrize("k_min,k_max", [(True, 3), (2, False), (2.5, 3), (2, "3")])
def test_analysis_range_rejects_non_integer_and_bool_bounds(
    matrix: np.ndarray, k_min: object, k_max: object
) -> None:
    with pytest.raises(ValueError, match="integer"):
        analyze_candidate_k(matrix, k_min, k_max)  # type: ignore[arg-type]


def test_analysis_rejects_silhouette_boundary_before_fitting(monkeypatch) -> None:
    fitted = False

    def unexpected_fit(*args, **kwargs):
        nonlocal fitted
        fitted = True
        raise AssertionError("K-Means must not run for an invalid analysis range")

    monkeypatch.setattr("src.clustering.run_kmeans", unexpected_fit)
    with pytest.raises(ValueError, match="silhouette is undefined"):
        analyze_candidate_k(np.eye(4), 2, 4)
    assert fitted is False


def test_solver_override_does_not_mutate_canonical_defaults(matrix: np.ndarray) -> None:
    before = get_default_solver_kwargs()
    fit = run_kmeans(matrix, 3, {"max_iter": 20, "tol": 0.001})
    after = get_default_solver_kwargs()

    assert fit.model.max_iter == 20
    assert fit.model.tol == 0.001
    assert before == after
    assert before is not after


@pytest.mark.parametrize(
    "metrics",
    [
        {},
        {"k": [2]},
        {"silhouette": [0.5]},
        {"k": [], "silhouette": []},
        {"k": [2, 3], "silhouette": [0.5]},
        {"k": [2], "silhouette": [np.nan]},
        {"k": [2], "silhouette": [np.inf]},
        {"k": [2], "silhouette": [-np.inf]},
    ],
)
def test_recommendation_rejects_malformed_analysis(metrics: dict) -> None:
    with pytest.raises(ValueError):
        recommend_k(metrics)


def _populated_state(matrix: np.ndarray):
    state = new_app_state()
    set_raw_dataset(state, "raw", "dataset")
    set_preprocessed_data(state, "processed", matrix, "preprocessed")
    metrics = analyze_candidate_k(matrix, 2, 4)
    set_k_analysis(state, metrics, recommend_k(metrics))
    set_selected_k(state, 3)
    set_clustering_result(
        state,
        "model",
        np.zeros(len(matrix), dtype=int),
        "profiles",
        run_metadata={"k": 3},
        results="results",
    )
    set_results(state, "results", "export")
    return state, metrics


def test_new_k_analysis_invalidates_all_downstream_artifacts(matrix: np.ndarray) -> None:
    state, old_metrics = _populated_state(matrix)
    new_metrics = analyze_candidate_k(matrix, 2, 3)
    new_recommendation = recommend_k(new_metrics)

    set_k_analysis(state, new_metrics, new_recommendation)

    assert state.k_metrics is new_metrics and state.k_metrics is not old_metrics
    assert state.recommended_k == new_recommendation
    assert state.selected_k is None
    assert state.model is state.labels is state.cluster_profiles is None
    assert state.run_metadata is state.results is state.export_payload is None


def test_selected_k_change_retains_analysis_and_invalidates_outputs(matrix: np.ndarray) -> None:
    state, metrics = _populated_state(matrix)
    recommendation = state.recommended_k

    set_selected_k(state, 4)

    assert state.k_metrics is metrics
    assert state.recommended_k == recommendation
    assert state.selected_k == 4
    assert state.model is state.labels is state.cluster_profiles is None
    assert state.run_metadata is state.results is state.export_payload is None


def test_selected_k_must_belong_to_analyzed_http_range() -> None:
    with TestClient(app) as client:
        assert client.post("/api/dataset/sample").status_code == 200
        assert client.post("/api/preprocess").status_code == 200
        analyzed = client.post("/api/k-analysis", json={"k_min": 3, "k_max": 6})
        assert analyzed.status_code == 200
        assert [row["k"] for row in analyzed.json()["k_analysis_data"]["k_metrics"]] == [
            3,
            4,
            5,
            6,
        ]
        assert client.post("/api/select-k", json={"selected_k": 5}).status_code == 200

        rejected = client.post("/api/select-k", json={"selected_k": 8})
        state = client.get("/api/state").json()

        assert rejected.status_code == 422
        assert state["selected_k"] == 5
        assert state["clustered"] is False
        assert state["results_ready"] is False
