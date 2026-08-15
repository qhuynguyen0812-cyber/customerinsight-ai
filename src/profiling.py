"""TV4 clustering orchestration, RFM profiling, and interpretation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score

from components.results_export import build_customer_results, validate_profile
from src.clustering import get_default_solver_kwargs, run_kmeans
from src.state import AppState, set_clustering_result

RFM_COLUMNS = ["Recency", "Frequency", "Monetary"]
PROFILE_REQUIRED_COLUMNS = [
    "Cluster", "SegmentName", "count", "mean Recency", "mean Frequency", "mean Monetary"
]


def _validated_business_data(data: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValueError("Processed customer data must be a non-empty DataFrame.")
    missing = [column for column in ["CustomerID", *RFM_COLUMNS] if column not in data.columns]
    if missing:
        raise ValueError("Processed customer data is missing: " + ", ".join(missing))
    if data[["CustomerID", *RFM_COLUMNS]].isna().any().any():
        raise ValueError("Processed customer data cannot contain missing CustomerID or RFM values.")
    if data["CustomerID"].duplicated().any():
        raise ValueError("CustomerID values must be unique.")
    numeric = data[RFM_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("RFM values must be finite numbers.")
    result = data.loc[:, ["CustomerID", *RFM_COLUMNS]].copy(deep=True)
    result[RFM_COLUMNS] = numeric
    return result


def _validated_labels(labels: Sequence[int] | np.ndarray, row_count: int) -> np.ndarray:
    values = np.asarray(labels)
    if values.ndim != 1 or len(values) != row_count:
        raise ValueError(f"Labels must be one-dimensional and match all {row_count} processed rows.")
    if len(values) == 0 or not np.issubdtype(values.dtype, np.integer):
        raise ValueError("Labels must contain integer cluster identifiers.")
    if (values < 0).any():
        raise ValueError("Cluster identifiers cannot be negative.")
    return values.astype(int, copy=True)


def _semantic_names(profile: pd.DataFrame) -> dict[int, str]:
    """Derive deterministic, evidence-limited names from relative RFM ranks."""
    ranked = profile.sort_values(
        ["mean Monetary", "mean Frequency", "mean Recency", "Cluster"],
        ascending=[False, False, True, True],
        kind="stable",
    )
    percentiles = profile.set_index("Cluster")[[
        "mean Recency", "mean Frequency", "mean Monetary"
    ]].rank(method="average", pct=True)
    names: dict[int, str] = {}
    used: dict[str, int] = {}
    for cluster in ranked["Cluster"].astype(int):
        scores = percentiles.loc[cluster]
        recency = "hoạt động gần đây" if scores["mean Recency"] <= 0.5 else "ít hoạt động gần đây"
        frequency = "tần suất cao" if scores["mean Frequency"] > 0.5 else "tần suất thấp"
        monetary = "giá trị cao" if scores["mean Monetary"] > 0.5 else "giá trị thấp"
        base = f"{monetary.capitalize()} – {recency}, {frequency}"
        occurrence = used.get(base, 0) + 1
        used[base] = occurrence
        # Ties are distinguished by their deterministic profile rank, never by raw label meaning.
        names[cluster] = base if occurrence == 1 else f"{base} (nhóm {occurrence})"
    return names


def compute_cluster_profiles(
    processed_df: pd.DataFrame, cluster_labels: Sequence[int] | np.ndarray
) -> pd.DataFrame:
    """Build one TV6-compatible profile row per observed cluster."""
    customers = _validated_business_data(processed_df)
    labels = _validated_labels(cluster_labels, len(customers))
    working = customers.assign(Cluster=labels)
    grouped = working.groupby("Cluster", sort=True, observed=True)
    profile = grouped[RFM_COLUMNS].agg(["mean", "median", "min", "max", "std"])
    profile.columns = [f"{stat} {feature}" for feature, stat in profile.columns]
    profile = profile.reset_index()
    profile.insert(1, "count", grouped.size().to_numpy())
    profile.insert(2, "percentage", profile["count"] / len(working) * 100.0)
    profile = profile.fillna({f"std {feature}": 0.0 for feature in RFM_COLUMNS})
    names = _semantic_names(profile)
    profile.insert(1, "SegmentName", profile["Cluster"].map(names))
    profile = profile.loc[:, PROFILE_REQUIRED_COLUMNS + [
        column for column in profile.columns if column not in PROFILE_REQUIRED_COLUMNS
    ]]
    validate_profile(profile)
    if int(profile["count"].sum()) != len(working):
        raise ValueError("Profile counts do not cover every processed row.")
    return profile


def generate_business_interpretation(profile_df: pd.DataFrame) -> dict[int, dict[str, str]]:
    """Return deterministic RFM descriptions and cautious suggested actions."""
    profile = validate_profile(profile_df)
    names = _semantic_names(profile)
    return {
        int(row["Cluster"]): {
            "segment_name": names[int(row["Cluster"])],
            "characteristics": names[int(row["Cluster"])],
            "recommendation": (
                "Ưu tiên duy trì tương tác và cân nhắc cơ hội gia tăng giá trị."
                if row["mean Monetary"] >= profile["mean Monetary"].median()
                else "Cân nhắc chiến dịch nuôi dưỡng hoặc tái kích hoạt phù hợp."
            ),
        }
        for _, row in profile.iterrows()
    }


def run_clustering_workflow(state: AppState) -> dict[str, Any]:
    """Compute all TV4/TV6 artifacts locally, then commit them atomically."""
    if state.scaled_matrix is None:
        raise ValueError("Scaled features are required before clustering.")
    if state.selected_k is None:
        raise ValueError("A confirmed K is required before clustering.")
    if state.raw_df is None:
        raise ValueError("Validated raw customers are required before clustering.")
    customers = _validated_business_data(state.processed_df)
    if len(state.scaled_matrix) != len(customers):
        raise ValueError("Scaled features and processed customer rows are not aligned.")

    started = perf_counter()
    fit = run_kmeans(state.scaled_matrix, state.selected_k, state.solver_preferences)
    silhouette = float(silhouette_score(state.scaled_matrix, fit.labels))
    profiles = compute_cluster_profiles(customers, fit.labels)
    interpretation = generate_business_interpretation(profiles)
    assignments = customers[["CustomerID"]].assign(
        Cluster=fit.labels,
        SegmentName=pd.Series(fit.labels).map(
            profiles.set_index("Cluster")["SegmentName"]
        ).to_numpy(),
    )
    results = build_customer_results(
        state.raw_df.loc[:, ["CustomerID", *RFM_COLUMNS]], assignments
    )
    effective = get_default_solver_kwargs()
    if isinstance(state.solver_preferences, Mapping):
        effective.update(state.solver_preferences)
    metadata = {
        "k": int(state.selected_k), **effective, "inertia": fit.inertia,
        "silhouette": silhouette, "iterations": fit.iterations,
        "runtime_seconds": perf_counter() - started,
    }
    set_clustering_result(
        state, fit.model, fit.labels, profiles,
        run_metadata=metadata, results=results,
    )
    return {"profiles": profiles, "interpretation": interpretation, "metadata": metadata}
