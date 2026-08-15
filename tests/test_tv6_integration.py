from __future__ import annotations

import codecs
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from components.results_export import CUSTOMER_RESULT_COLUMNS, customer_results_to_csv_bytes
from components.states import APP_STATE_KEY
from src.clustering import analyze_candidate_k, recommend_k
from src.preprocessing import run_pipeline_preprocessing
from src.profiling import run_clustering_workflow
from src.state import (
    new_app_state, set_k_analysis, set_preprocessed_data, set_raw_dataset,
    set_selected_k, set_solver_preferences,
)
from src.validation import load_sample_dataset


ROOT = Path(__file__).resolve().parents[1]


def _completed_state():
    validated = load_sample_dataset(ROOT / "data" / "sample_customers.csv")
    preprocessing = run_pipeline_preprocessing(validated.raw_df)
    state = new_app_state()
    set_raw_dataset(state, validated.raw_df, validated.dataset_signature)
    set_preprocessed_data(
        state, preprocessing["processed_df"], preprocessing["scaled_matrix"],
        preprocessing["preprocessing_signature"],
    )
    metrics = analyze_candidate_k(state.scaled_matrix, 2, 10)
    set_k_analysis(state, metrics, recommend_k(metrics))
    set_selected_k(state, 3)
    run_clustering_workflow(state)
    return state


def test_real_720_row_data_to_export_flow() -> None:
    validated = load_sample_dataset(ROOT / "data" / "sample_customers.csv")
    state = new_app_state()
    set_raw_dataset(state, validated.raw_df, validated.dataset_signature)
    preprocessing = run_pipeline_preprocessing(state.raw_df)
    set_preprocessed_data(
        state,
        preprocessing["processed_df"],
        preprocessing["scaled_matrix"],
        preprocessing["preprocessing_signature"],
    )
    metrics = analyze_candidate_k(state.scaled_matrix, 2, 10)
    set_k_analysis(state, metrics, recommend_k(metrics))
    set_selected_k(state, state.recommended_k)
    run_clustering_workflow(state)

    assert len(state.raw_df) == len(state.processed_df) == len(state.labels) == 720
    assert state.scaled_matrix.shape == (720, 3)
    assert state.recommended_k == state.selected_k == 3
    assert state.run_metadata["inertia"] == pytest.approx(611.4205381920901, abs=1e-12)
    assert state.run_metadata["silhouette"] == pytest.approx(0.45877917738169266, abs=1e-12)
    assert state.run_metadata["iterations"] == 9
    assert int(state.cluster_profiles["count"].sum()) == len(state.results) == 720
    assert state.results["CustomerID"].is_unique
    assert state.results["SegmentName"].notna().all()
    assert list(state.results.columns) == CUSTOMER_RESULT_COLUMNS
    expected_raw = state.raw_df.set_index("CustomerID")[["Recency", "Frequency", "Monetary"]]
    actual_raw = state.results.set_index("CustomerID")[["Recency", "Frequency", "Monetary"]]
    pd.testing.assert_frame_equal(actual_raw, expected_raw)

    payload = customer_results_to_csv_bytes(state.results)
    assert payload.startswith(codecs.BOM_UTF8) and b"\r\n" not in payload
    exported = pd.read_csv(BytesIO(payload), encoding="utf-8-sig")
    assert exported.shape == (720, 6)
    assert list(exported.columns) == CUSTOMER_RESULT_COLUMNS


def test_production_profiles_processed_values_but_results_preserve_raw_values() -> None:
    raw = pd.DataFrame({
        "CustomerID": [f"C-{index}" for index in range(6)],
        "Recency": [1.0, 2.0, None, 4.0, 5.0, 1000.0],
        "Frequency": [1.0, 2.0, 3.0, 4.0, 5.0, 1000.0],
        "Monetary": [10.0, 20.0, 30.0, 40.0, 50.0, 10000.0],
    })
    preprocessing = run_pipeline_preprocessing(raw)
    state = new_app_state()
    set_raw_dataset(state, raw, "raw-with-missing-and-outlier")
    set_preprocessed_data(
        state, preprocessing["processed_df"], preprocessing["scaled_matrix"],
        preprocessing["preprocessing_signature"],
    )
    set_k_analysis(state, {"k": [2], "inertia": [1.0], "silhouette": [0.5]}, 2)
    set_selected_k(state, 2)
    run_clustering_workflow(state)

    assert state.processed_df.loc[2, "Recency"] != state.raw_df.loc[2, "Recency"]
    assert state.processed_df.loc[5, "Monetary"] != state.raw_df.loc[5, "Monetary"]
    pd.testing.assert_frame_equal(state.results.iloc[:, :4], state.raw_df)


@pytest.mark.parametrize("dependency", ["dataset", "preprocessing", "selected_k", "solver"])
def test_upstream_changes_invalidate_results_and_hide_export(dependency: str) -> None:
    state = _completed_state()
    if dependency == "dataset":
        set_raw_dataset(state, state.raw_df.copy(deep=True), "changed-dataset")
    elif dependency == "preprocessing":
        set_preprocessed_data(
            state, state.processed_df.copy(deep=True), state.scaled_matrix.copy(),
            "changed-preprocessing",
        )
    elif dependency == "selected_k":
        set_selected_k(state, 2)
    else:
        set_solver_preferences(state, {"n_init": 20})

    for field in (
        "model", "labels", "cluster_profiles", "run_metadata", "results", "export_payload"
    ):
        assert getattr(state, field) is None

    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py"))
    app.session_state[APP_STATE_KEY] = state
    app.run()
    assert not app.exception
    assert len(app.info) == 1
    assert len(app.get("download_button")) == 0
