"""TV6 customer-result validation and CSV export helpers.

These helpers consume a completed result table. They deliberately do not fit a
model, derive labels, or own web session state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd


CUSTOMER_RESULT_COLUMNS = [
    "CustomerID",
    "Recency",
    "Frequency",
    "Monetary",
    "Cluster",
    "SegmentName",
]

PROFILE_REQUIRED_COLUMNS = [
    "Cluster",
    "SegmentName",
    "count",
    "mean Recency",
    "mean Frequency",
    "mean Monetary",
]

RUN_METADATA_FIELDS = [
    "k",
    "init",
    "n_init",
    "random_state",
    "max_iter",
    "tol",
    "inertia",
    "silhouette",
    "iterations",
    "runtime_seconds",
]
RAW_CUSTOMER_COLUMNS = ["CustomerID", "Recency", "Frequency", "Monetary"]
ASSIGNMENT_COLUMNS = ["CustomerID", "Cluster", "SegmentName"]


class ResultContractError(ValueError):
    """Raised when an upstream result violates the locked output contract."""


def build_customer_results(raw_customers: pd.DataFrame, assignments: pd.DataFrame) -> pd.DataFrame:
    """Map current assignments one-to-one while preserving active raw RFM."""
    if not isinstance(raw_customers, pd.DataFrame) or list(raw_customers.columns) != RAW_CUSTOMER_COLUMNS:
        raise ResultContractError("Active raw customers must contain the four canonical columns.")
    if not isinstance(assignments, pd.DataFrame) or list(assignments.columns) != ASSIGNMENT_COLUMNS:
        raise ResultContractError("Assignments must contain CustomerID, Cluster, SegmentName.")
    if raw_customers.empty or assignments.empty:
        raise ResultContractError("Active customers and assignments cannot be empty.")
    if raw_customers["CustomerID"].isna().any() or raw_customers["CustomerID"].duplicated().any():
        raise ResultContractError("Active CustomerID values must be non-null and unique.")
    if assignments["CustomerID"].isna().any() or assignments["CustomerID"].duplicated().any():
        raise ResultContractError("Assignment CustomerID values must be non-null and unique.")
    if assignments[["Cluster", "SegmentName"]].isna().any().any():
        raise ResultContractError("Every assignment needs a current Cluster and SegmentName.")

    try:
        mapped = raw_customers.merge(
            assignments,
            on="CustomerID",
            how="left",
            sort=False,
            validate="one_to_one",
        )
    except pd.errors.MergeError as error:
        raise ResultContractError("Customer assignments are not one-to-one.") from error
    if len(mapped) != len(raw_customers) or mapped[["Cluster", "SegmentName"]].isna().any().any():
        raise ResultContractError("Assignments must map every active customer exactly once.")
    if set(assignments["CustomerID"]) != set(raw_customers["CustomerID"]):
        raise ResultContractError("Assignments contain a stale or unknown CustomerID.")
    return validate_customer_results(mapped)


def validate_customer_results(results: pd.DataFrame) -> pd.DataFrame:
    """Return a defensive canonical copy of a valid customer result table."""
    if not isinstance(results, pd.DataFrame):
        raise ResultContractError("Customer results must be a pandas DataFrame.")

    actual_columns = list(results.columns)
    if actual_columns != CUSTOMER_RESULT_COLUMNS:
        raise ResultContractError(
            "Customer results must contain exactly these columns in order: "
            + ", ".join(CUSTOMER_RESULT_COLUMNS)
        )
    if results.empty:
        raise ResultContractError("Customer results are empty.")
    if results["CustomerID"].isna().any():
        raise ResultContractError("CustomerID cannot be missing.")
    if results["CustomerID"].duplicated().any():
        raise ResultContractError("CustomerID must map one-to-one to results.")
    if results[["Cluster", "SegmentName"]].isna().any().any():
        raise ResultContractError("Customer results cannot contain incomplete assignments.")

    return results.loc[:, CUSTOMER_RESULT_COLUMNS].copy(deep=True)


def customer_results_to_csv_bytes(results: pd.DataFrame) -> bytes:
    """Serialize current validated results as deterministic UTF-8 BOM CSV."""
    canonical = validate_customer_results(results)
    return canonical.to_csv(index=False, lineterminator="\n").encode("utf-8-sig")


def validate_profile(profile: pd.DataFrame) -> pd.DataFrame:
    """Validate the minimum TV4 profile handoff without recomputing it."""
    if not isinstance(profile, pd.DataFrame):
        raise ResultContractError("Cluster profile must be a pandas DataFrame.")
    missing = [column for column in PROFILE_REQUIRED_COLUMNS if column not in profile.columns]
    if missing:
        raise ResultContractError("Cluster profile is missing: " + ", ".join(missing))
    if profile.empty:
        raise ResultContractError("Cluster profile is empty.")
    if profile[PROFILE_REQUIRED_COLUMNS].isna().any().any():
        raise ResultContractError("Cluster profile contains null required values.")
    if profile["Cluster"].duplicated().any():
        raise ResultContractError("Cluster profile must contain one row per cluster.")
    return profile.copy(deep=True)


def available_run_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return the locked minimum production run metadata."""
    if not isinstance(metadata, Mapping):
        raise ResultContractError("Run metadata must be a mapping.")
    missing = [field for field in RUN_METADATA_FIELDS if field not in metadata]
    if missing:
        raise ResultContractError("Run metadata is missing: " + ", ".join(missing))
    null_fields = [field for field in RUN_METADATA_FIELDS if metadata[field] is None]
    if null_fields:
        raise ResultContractError("Run metadata contains null values: " + ", ".join(null_fields))
    return {field: metadata[field] for field in RUN_METADATA_FIELDS}
