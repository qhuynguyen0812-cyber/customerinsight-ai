from __future__ import annotations

import codecs
from io import BytesIO

import pandas as pd
import pytest

from components.results_export import (
    CUSTOMER_RESULT_COLUMNS,
    ResultContractError,
    available_run_metadata,
    build_customer_results,
    customer_results_to_csv_bytes,
    validate_customer_results,
)


@pytest.fixture
def results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerID": ["C-001", "C-002"],
            "Recency": [3.0, 12.0],
            "Frequency": [9.0, 2.0],
            "Monetary": [120.5, 40.0],
            "Cluster": [1, 0],
            "SegmentName": ["Active", "Low engagement"],
        }
    )


def test_customer_result_contract_preserves_mapping_and_raw_rfm(results: pd.DataFrame) -> None:
    validated = validate_customer_results(results)
    assert list(validated.columns) == CUSTOMER_RESULT_COLUMNS
    pd.testing.assert_frame_equal(validated, results)
    assert validated["CustomerID"].is_unique
    assert len(validated) == len(results)


def test_customer_mapping_joins_current_assignments_to_raw_rfm(results: pd.DataFrame) -> None:
    raw = results.loc[:, ["CustomerID", "Recency", "Frequency", "Monetary"]]
    assignments = results.loc[:, ["CustomerID", "Cluster", "SegmentName"]].iloc[::-1]
    mapped = build_customer_results(raw, assignments)
    pd.testing.assert_frame_equal(mapped, results)


def test_customer_mapping_preserves_raw_order_and_unimputed_values() -> None:
    raw = pd.DataFrame({
        "CustomerID": ["C-002", "C-001"],
        "Recency": [None, 999.0],
        "Frequency": [2.0, 3.0],
        "Monetary": [40.0, 5000.0],
    })
    assignments = pd.DataFrame({
        "CustomerID": ["C-001", "C-002"],
        "Cluster": [1, 0],
        "SegmentName": ["High", "Low"],
    })
    mapped = build_customer_results(raw, assignments)
    assert mapped["CustomerID"].tolist() == ["C-002", "C-001"]
    pd.testing.assert_frame_equal(mapped.iloc[:, :4], raw)


def test_customer_mapping_rejects_stale_or_incomplete_assignments(results: pd.DataFrame) -> None:
    raw = results.loc[:, ["CustomerID", "Recency", "Frequency", "Monetary"]]
    assignments = results.loc[:, ["CustomerID", "Cluster", "SegmentName"]].iloc[[0]]
    with pytest.raises(ResultContractError, match="every active customer"):
        build_customer_results(raw, assignments)


@pytest.mark.parametrize("kind", ["duplicate", "null", "unknown"])
def test_customer_mapping_rejects_invalid_assignment_ids(
    results: pd.DataFrame, kind: str
) -> None:
    raw = results.loc[:, ["CustomerID", "Recency", "Frequency", "Monetary"]]
    assignments = results.loc[:, ["CustomerID", "Cluster", "SegmentName"]].copy()
    if kind == "duplicate":
        assignments.loc[1, "CustomerID"] = assignments.loc[0, "CustomerID"]
    elif kind == "null":
        assignments.loc[1, "CustomerID"] = None
    else:
        assignments.loc[1, "CustomerID"] = "STALE"
    with pytest.raises(ResultContractError):
        build_customer_results(raw, assignments)


def test_customer_export_has_bom_no_index_and_round_trips(results: pd.DataFrame) -> None:
    payload = customer_results_to_csv_bytes(results)
    assert payload == customer_results_to_csv_bytes(results)
    assert payload.startswith(codecs.BOM_UTF8)
    assert b"\r\n" not in payload
    exported = pd.read_csv(BytesIO(payload), encoding="utf-8-sig", dtype={"CustomerID": str})
    assert list(exported.columns) == CUSTOMER_RESULT_COLUMNS
    assert not any(column.startswith("Unnamed:") for column in exported.columns)
    pd.testing.assert_frame_equal(exported, results)


def test_duplicate_customer_mapping_is_rejected(results: pd.DataFrame) -> None:
    invalid = pd.concat([results, results.iloc[[0]]], ignore_index=True)
    with pytest.raises(ResultContractError, match="one-to-one"):
        validate_customer_results(invalid)


def test_exact_output_schema_is_required(results: pd.DataFrame) -> None:
    with pytest.raises(ResultContractError, match="exactly"):
        validate_customer_results(results.assign(Unexpected="value"))


@pytest.fixture
def run_metadata() -> dict[str, object]:
    return {
        "k": 4,
        "init": "k-means++",
        "n_init": 10,
        "random_state": 42,
        "max_iter": 300,
        "tol": 0.0001,
        "inertia": 8.5,
        "silhouette": 0.61,
        "iterations": 7,
        "runtime_seconds": 0.04,
    }


def test_full_run_metadata_contract_passes_without_inventing_values(
    run_metadata: dict[str, object],
) -> None:
    supplied = {**run_metadata, "optional_note": "upstream-only"}
    validated = available_run_metadata(supplied)
    assert validated == run_metadata
    assert "optional_note" not in validated


def test_missing_required_run_metadata_field_fails(run_metadata: dict[str, object]) -> None:
    incomplete = dict(run_metadata)
    incomplete.pop("runtime_seconds")
    with pytest.raises(ResultContractError, match="missing: runtime_seconds"):
        available_run_metadata(incomplete)


def test_null_required_run_metadata_field_fails(run_metadata: dict[str, object]) -> None:
    invalid = {**run_metadata, "silhouette": None}
    with pytest.raises(ResultContractError, match="null values: silhouette"):
        available_run_metadata(invalid)
