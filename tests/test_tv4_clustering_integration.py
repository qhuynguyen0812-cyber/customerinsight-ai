"""TV2 -> TV3 -> TV4 -> TV6 integration tests."""

from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import silhouette_score
from streamlit.testing.v1 import AppTest

from components.results_export import validate_customer_results, validate_profile
from components.states import APP_STATE_KEY
from src.clustering import analyze_candidate_k, recommend_k, run_kmeans
from src.preprocessing import run_pipeline_preprocessing
from src.profiling import run_clustering_workflow
from src.state import (
    new_app_state, set_clustering_result, set_k_analysis, set_preprocessed_data,
    set_raw_dataset, set_selected_k,
)
from src.validation import load_sample_dataset

ROOT = Path(__file__).resolve().parents[1]


def ready_state():
    validated = load_sample_dataset(ROOT / "data" / "sample_customers.csv")
    processed = run_pipeline_preprocessing(validated.raw_df)
    state = new_app_state()
    set_raw_dataset(state, validated.raw_df, validated.dataset_signature)
    set_preprocessed_data(
        state, processed["processed_df"], processed["scaled_matrix"],
        processed["preprocessing_signature"],
    )
    metrics = analyze_candidate_k(state.scaled_matrix, 2, 10)
    set_k_analysis(state, metrics, recommend_k(metrics))
    set_selected_k(state, 3)
    return state


def test_canonical_tv4_pipeline_and_tv6_handoff() -> None:
    state = ready_state()
    direct = run_kmeans(state.scaled_matrix, state.selected_k)
    assert direct.inertia == pytest.approx(611.4205381920901, abs=1e-12)
    assert silhouette_score(state.scaled_matrix, direct.labels) == pytest.approx(
        0.45877917738169266, abs=1e-12
    )
    assert direct.iterations == 9

    output = run_clustering_workflow(state)
    assert len(state.processed_df) == len(state.labels) == len(state.results) == 720
    assert state.scaled_matrix.shape == (720, 3)
    assert state.recommended_k == state.selected_k == 3
    assert state.cluster_profiles["count"].sum() == 720
    assert state.cluster_profiles["Cluster"].nunique() == 3
    assert state.cluster_profiles["SegmentName"].notna().all()
    validate_profile(state.cluster_profiles)
    validate_customer_results(state.results)
    assert output["metadata"]["inertia"] == pytest.approx(611.4205381920901, abs=1e-12)
    assert output["metadata"]["iterations"] == 9


def test_failed_orchestration_does_not_partial_commit(monkeypatch) -> None:
    state = ready_state()
    set_clustering_result(state, "old-model", np.zeros(720, dtype=int), "old-profile")
    import src.profiling as profiling
    monkeypatch.setattr(
        profiling, "compute_cluster_profiles",
        lambda *_: (_ for _ in ()).throw(ValueError("profile failure")),
    )
    with pytest.raises(ValueError, match="profile failure"):
        run_clustering_workflow(state)
    assert state.model == "old-model"
    assert state.cluster_profiles == "old-profile"


def test_page_gating_and_explicit_cta() -> None:
    page = ROOT / "views" / "4_Phan_cum.py"
    empty = AppTest.from_file(str(page)).run()
    assert not empty.exception and len(empty.button) == 0

    state = ready_state()
    app = AppTest.from_file(str(page))
    app.session_state[APP_STATE_KEY] = state
    app.run()
    assert not app.exception
    assert state.model is None
    assert app.button[0].label == "Chạy K-Means"
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert state.model is not None and state.results is not None


def test_tv4_has_no_second_kmeans_implementation() -> None:
    for path in [ROOT / "src" / "profiling.py", ROOT / "views" / "4_Phan_cum.py"]:
        source = path.read_text(encoding="utf-8")
        assert "KMeans(" not in source
        assert "from src.clustering import" in source
