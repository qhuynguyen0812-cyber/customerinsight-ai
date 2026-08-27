"""TV4 Phase 2 clustering orchestration and handoff evidence."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import src.profiling as profiling
from components.results_export import RUN_METADATA_FIELDS, available_run_metadata
from src.preprocessing import run_pipeline_preprocessing
from src.profiling import run_clustering_workflow
from src.state import AppState
from src.validation import load_sample_dataset


ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def canonical_data() -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    raw = load_sample_dataset(ROOT / "data" / "sample_customers.csv").raw_df
    preprocessed = run_pipeline_preprocessing(raw)
    return raw, preprocessed["processed_df"], preprocessed["scaled_matrix"]


def _state(
    canonical_data: tuple[pd.DataFrame, pd.DataFrame, np.ndarray],
    k: int = 3,
    solver_preferences: dict[str, object] | None = None,
) -> AppState:
    raw, processed, scaled = canonical_data
    return AppState(
        raw_df=raw.copy(deep=True),
        dataset_signature="canonical",
        processed_df=processed.copy(deep=True),
        scaled_matrix=scaled.copy(),
        preprocessing_signature="default",
        k_metrics={"k": [3, 5]},
        selected_k=k,
        solver_preferences=solver_preferences,
    )


def _old_artifacts(state: AppState) -> dict[str, object]:
    old = {
        "model": object(),
        "labels": np.array([91, 92]),
        "cluster_profiles": pd.DataFrame({"old": [1]}),
        "run_metadata": {"old": True},
        "results": pd.DataFrame({"old": [2]}),
        "export_payload": b"old-export",
    }
    for key, value in old.items():
        setattr(state, key, value)
    return old


def _assert_old_artifacts_preserved(state: AppState, old: dict[str, object]) -> None:
    for key, value in old.items():
        assert getattr(state, key) is value


def test_canonical_k3_workflow_and_typed_metadata(canonical_data) -> None:
    state = _state(canonical_data)

    output = run_clustering_workflow(state)

    assert len(state.raw_df) == 720
    assert state.model.n_clusters == 3
    assert len(np.unique(state.labels)) == 3
    assert len(state.cluster_profiles) == 3
    assert int(state.cluster_profiles["count"].sum()) == 720
    assert len(state.results) == 720
    assert state.results["CustomerID"].is_unique
    assert state.results["CustomerID"].equals(state.raw_df["CustomerID"])
    pd.testing.assert_frame_equal(
        state.results[["CustomerID", "Recency", "Frequency", "Monetary"]],
        state.raw_df[["CustomerID", "Recency", "Frequency", "Monetary"]],
    )
    assert state.run_metadata["inertia"] == pytest.approx(611.4205381920901)
    assert state.run_metadata["silhouette"] == pytest.approx(0.45877917738169266)
    assert state.run_metadata["iterations"] == 9
    assert output["metadata"] is state.run_metadata
    assert set(available_run_metadata(state.run_metadata)) == set(RUN_METADATA_FIELDS)
    expected_types = {
        "k": int,
        "init": str,
        "n_init": int,
        "random_state": int,
        "max_iter": int,
        "tol": float,
        "inertia": float,
        "silhouette": float,
        "iterations": int,
        "runtime_seconds": float,
    }
    for key, expected_type in expected_types.items():
        assert type(state.run_metadata[key]) is expected_type
    assert state.run_metadata["k"] == 3
    assert state.run_metadata["init"] == "k-means++"
    assert state.run_metadata["n_init"] == 10
    assert state.run_metadata["random_state"] == 42
    assert state.run_metadata["max_iter"] == 300
    assert state.run_metadata["tol"] == pytest.approx(0.0001)


def test_dynamic_k5_has_exact_profiles_and_mapping(canonical_data) -> None:
    state = _state(canonical_data, k=5)

    run_clustering_workflow(state)

    assert state.model.n_clusters == 5
    assert len(np.unique(state.labels)) == 5
    assert len(state.cluster_profiles) == 5
    assert int(state.cluster_profiles["count"].sum()) == 720
    assert len(state.results) == 720
    assert state.results["CustomerID"].is_unique
    assert state.run_metadata["k"] == 5


def test_solver_override_is_used_by_model_and_metadata(canonical_data) -> None:
    state = _state(canonical_data, solver_preferences={"max_iter": 400, "tol": 0.0002})

    run_clustering_workflow(state)

    assert state.model.max_iter == state.run_metadata["max_iter"] == 400
    assert state.model.tol == state.run_metadata["tol"] == pytest.approx(0.0002)
    assert state.run_metadata["init"] == "k-means++"
    assert state.run_metadata["n_init"] == 10
    assert state.run_metadata["random_state"] == 42


def test_fit_failure_preserves_every_prior_artifact(monkeypatch, canonical_data) -> None:
    state = _state(canonical_data)
    old = _old_artifacts(state)

    def fail_fit(*args, **kwargs):
        raise ValueError("controlled fit failure")

    monkeypatch.setattr(profiling, "run_kmeans", fail_fit)
    with pytest.raises(ValueError, match="controlled fit failure"):
        run_clustering_workflow(state)
    _assert_old_artifacts_preserved(state, old)


def test_profile_failure_preserves_every_prior_artifact(monkeypatch, canonical_data) -> None:
    state = _state(canonical_data)
    old = _old_artifacts(state)

    def fail_profile(*args, **kwargs):
        raise ValueError("controlled profile failure")

    monkeypatch.setattr(profiling, "compute_cluster_profiles", fail_profile)
    with pytest.raises(ValueError, match="controlled profile failure"):
        run_clustering_workflow(state)
    _assert_old_artifacts_preserved(state, old)


def test_mapping_failure_preserves_every_prior_artifact(monkeypatch, canonical_data) -> None:
    state = _state(canonical_data)
    old = _old_artifacts(state)

    def fail_mapping(*args, **kwargs):
        raise ValueError("controlled mapping failure")

    monkeypatch.setattr(profiling, "build_customer_results", fail_mapping)
    with pytest.raises(ValueError, match="controlled mapping failure"):
        run_clustering_workflow(state)
    _assert_old_artifacts_preserved(state, old)


def test_degenerate_fit_is_rejected_without_fake_silhouette(monkeypatch, canonical_data) -> None:
    state = _state(canonical_data, k=3)
    old = _old_artifacts(state)
    labels = np.arange(len(state.processed_df), dtype=int) % 2
    fake_model = SimpleNamespace(get_params=lambda: {})
    fake_fit = SimpleNamespace(model=fake_model, labels=labels, inertia=1.0, iterations=1)
    monkeypatch.setattr(profiling, "run_kmeans", lambda *args, **kwargs: fake_fit)

    with pytest.raises(ValueError, match="2 distinct clusters for selected K=3"):
        run_clustering_workflow(state)

    _assert_old_artifacts_preserved(state, old)


def test_successful_rerun_invalidates_stale_export(canonical_data) -> None:
    state = _state(canonical_data)
    state.export_payload = b"stale-export"

    run_clustering_workflow(state)

    assert state.export_payload is None


def test_interpretation_is_evidence_limited_and_label_independent() -> None:
    customers = pd.DataFrame({
        "CustomerID": ["A", "B", "C", "D"],
        "Recency": [1.0, 2.0, 20.0, 30.0],
        "Frequency": [10.0, 8.0, 2.0, 1.0],
        "Monetary": [100.0, 80.0, 20.0, 10.0],
    })
    first = profiling.compute_cluster_profiles(customers, [0, 0, 1, 1])
    relabeled = profiling.compute_cluster_profiles(customers, [9, 9, 4, 4])
    assert first.loc[first["mean Monetary"].idxmax(), "SegmentName"] == relabeled.loc[
        relabeled["mean Monetary"].idxmax(), "SegmentName"
    ]
    text = str(profiling.generate_business_interpretation(first)).lower()
    assert all(term not in text for term in ["sale hunter", "săn sale", "khuyến mãi", "giảm giá", "churn"])
