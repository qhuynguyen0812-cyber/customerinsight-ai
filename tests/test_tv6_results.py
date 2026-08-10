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


def test_customer_mapping_rejects_stale_or_incomplete_assignments(results: pd.DataFrame) -> None:
    raw = results.loc[:, ["CustomerID", "Recency", "Frequency", "Monetary"]]
    assignments = results.loc[:, ["CustomerID", "Cluster", "SegmentName"]].iloc[[0]]
    with pytest.raises(ResultContractError, match="every active customer"):
        build_customer_results(raw, assignments)


def test_customer_export_has_bom_no_index_and_round_trips(results: pd.DataFrame) -> None:
    payload = customer_results_to_csv_bytes(results)
    assert payload.startswith(codecs.BOM_UTF8)
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


def test_metadata_never_invents_unavailable_values() -> None:
    assert available_run_metadata({"k": 4, "inertia": 8.5}) == {"k": 4, "inertia": 8.5}
