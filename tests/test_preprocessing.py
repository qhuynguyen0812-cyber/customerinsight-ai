"""TV2 Phase 1 preprocessing and integration contract tests."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.preprocessing import (
    PreprocessingError,
    RFM_FEATURES,
    handle_missing_values,
    handle_outliers_iqr,
    run_pipeline_preprocessing,
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
from src.validation import load_sample_dataset

ROOT = Path(__file__).resolve().parents[1]


def raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerID": ["A", "B", "C", "D", "E"],
            "Recency": [1.0, 2.0, np.nan, 4.0, 100.0],
            "Frequency": [1.0, np.nan, 3.0, 4.0, 5.0],
            "Monetary": [10.0, 20.0, 30.0, np.nan, 50.0],
        }
    )


def test_module_and_canonical_features() -> None:
    assert RFM_FEATURES == ("Recency", "Frequency", "Monetary")


def test_median_imputation_is_per_feature_and_preserves_identity() -> None:
    raw = raw_frame()
    result = handle_missing_values(raw)

    assert result.loc[2, "Recency"] == 3.0
    assert result.loc[1, "Frequency"] == 3.5
    assert result.loc[3, "Monetary"] == 25.0
    assert result["CustomerID"].equals(raw["CustomerID"])
    assert len(result) == len(raw)
    assert result.loc[:, list(RFM_FEATURES)].isna().sum().sum() == 0


def test_pipeline_clips_expected_iqr_bounds_without_dropping_rows() -> None:
    df = pd.DataFrame(
        {
            "CustomerID": ["A", "B", "C", "D", "E"],
            "Recency": [0.0, 1.0, 2.0, 3.0, 100.0],
            "Frequency": [1.0] * 5,
            "Monetary": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )
    clipped, bounds = handle_outliers_iqr(df)

    assert bounds["Recency"] == {
        "q1": 1.0,
        "q3": 3.0,
        "iqr": 2.0,
        "lower_bound": -2.0,
        "upper_bound": 6.0,
    }
    assert clipped["Recency"].iloc[-1] == 6.0
    assert bounds["Frequency"]["iqr"] == 0.0
    assert len(clipped) == len(df)
    assert clipped["CustomerID"].equals(df["CustomerID"])


def test_pipeline_output_is_finite_rfm_only_and_deterministic() -> None:
    raw = raw_frame()
    first = run_pipeline_preprocessing(raw)
    second = run_pipeline_preprocessing(raw.copy())

    assert len(first["processed_df"]) == len(raw)
    assert first["processed_df"]["CustomerID"].equals(raw["CustomerID"])
    assert first["scaled_matrix"].shape == (len(raw), 3)
    assert np.isfinite(first["scaled_matrix"]).all()
    assert tuple(first["scaler"].feature_names_in_) == RFM_FEATURES
    assert first["scaler"].n_features_in_ == 3
    assert list(first["scaled_df"].columns) == list(RFM_FEATURES)
    np.testing.assert_array_equal(first["scaled_matrix"], second["scaled_matrix"])
    assert first["preprocessing_signature"] == second["preprocessing_signature"]
    assert first["metadata"]["features"] == list(RFM_FEATURES)


@pytest.mark.parametrize("strategy", ["mean", "drop", "unknown"])
def test_unsupported_missing_strategy_fails_clearly(strategy: str) -> None:
    with pytest.raises(PreprocessingError, match="Unsupported missing strategy"):
        run_pipeline_preprocessing(raw_frame(), missing_strategy=strategy)


@pytest.mark.parametrize("strategy", ["none", "drop", "winsor"])
def test_unsupported_outlier_strategy_fails_clearly(strategy: str) -> None:
    with pytest.raises(PreprocessingError, match="Unsupported outlier strategy"):
        run_pipeline_preprocessing(raw_frame(), outlier_strategy=strategy)


def test_all_missing_feature_and_infinity_fail_before_scaling() -> None:
    raw = raw_frame()
    raw["Recency"] = np.nan
    with pytest.raises(PreprocessingError, match="no valid values"):
        run_pipeline_preprocessing(raw)

    raw = raw_frame()
    raw.loc[0, "Monetary"] = np.inf
    with pytest.raises(PreprocessingError, match="infinite"):
        run_pipeline_preprocessing(raw)


def test_canonical_tv1_sample_handoff_has_720_by_3_output() -> None:
    validated = load_sample_dataset(ROOT / "data" / "sample_customers.csv")
    result = run_pipeline_preprocessing(validated.raw_df)

    assert list(validated.raw_df.columns) == ["CustomerID", *RFM_FEATURES]
    assert len(validated.raw_df) == 720
    assert len(result["processed_df"]) == 720
    assert result["scaled_matrix"].shape == (720, 3)
    assert result["processed_df"]["CustomerID"].equals(validated.raw_df["CustomerID"])


def test_successful_commit_uses_canonical_setter_and_invalidates_downstream() -> None:
    raw = raw_frame()
    result = run_pipeline_preprocessing(raw)
    state = new_app_state()
    set_raw_dataset(state, raw, "dataset-a")
    set_preprocessed_data(state, pd.DataFrame(), np.zeros((1, 3)), "old")
    set_k_analysis(state, {"scores": [1]}, 2)
    set_selected_k(state, 2)
    set_clustering_result(
        state, "model", [0], "profiles", run_metadata={"run": "current"}
    )
    set_results(state, "results", "export")

    set_preprocessed_data(
        state,
        result["processed_df"],
        result["scaled_matrix"],
        result["preprocessing_signature"],
        result["eda_summary"],
    )

    assert state.scaled_matrix.shape == (len(raw), 3)
    assert state.eda_summary["scaler"] is result["scaler"]
    for value in (
        state.k_metrics,
        state.recommended_k,
        state.selected_k,
        state.model,
        state.labels,
        state.cluster_profiles,
        state.results,
        state.export_payload,
    ):
        assert value is None


def test_failed_preprocessing_leaves_previous_valid_state_unchanged() -> None:
    state = new_app_state()
    good = raw_frame()
    result = run_pipeline_preprocessing(good)
    set_raw_dataset(state, good, "dataset-a")
    set_preprocessed_data(
        state,
        result["processed_df"],
        result["scaled_matrix"],
        result["preprocessing_signature"],
    )
    previous_df = state.processed_df
    previous_matrix = state.scaled_matrix
    previous_signature = state.preprocessing_signature

    with pytest.raises(PreprocessingError):
        # This mirrors the page's compute-then-commit boundary: setter is never reached.
        failed = run_pipeline_preprocessing(good, missing_strategy="drop")
        set_preprocessed_data(
            state,
            failed["processed_df"],
            failed["scaled_matrix"],
            failed["preprocessing_signature"],
        )

    assert state.processed_df is previous_df
    assert state.scaled_matrix is previous_matrix
    assert state.preprocessing_signature == previous_signature
