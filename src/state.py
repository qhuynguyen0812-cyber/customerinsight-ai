"""Canonical, framework-independent state for the customer workflow.

Feature modules own the concrete data objects; TV5 owns their lifetime and
dependency rules.  Keeping this module free of Streamlit imports makes the
contract testable and lets every page use the same invalidation semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Final, Iterable


@dataclass
class AppState:
    """One complete snapshot of the canonical workflow."""

    # TV1: validated dataset
    raw_df: Any | None = None
    dataset_signature: str | None = None

    # TV2: preprocessing and EDA
    processed_df: Any | None = None
    scaled_matrix: Any | None = None
    preprocessing_signature: str | None = None
    eda_summary: Any | None = None

    # TV3: K analysis and confirmation
    k_metrics: Any | None = None
    recommended_k: int | None = None
    selected_k: int | None = None

    # User-owned input; it survives invalidation of solver output.
    solver_preferences: Any | None = None

    # TV4: clustering/profile output
    model: Any | None = None
    labels: Any | None = None
    cluster_profiles: Any | None = None
    run_metadata: Any | None = None

    # TV6: presentation/export output
    results: Any | None = None
    export_payload: Any | None = None


STATE_DEPENDENCIES: Final[dict[str, tuple[str, ...]]] = {
    "raw_df": (),
    "dataset_signature": ("raw_df",),
    "processed_df": ("raw_df", "dataset_signature"),
    "scaled_matrix": ("processed_df", "preprocessing_signature"),
    "preprocessing_signature": ("raw_df", "dataset_signature"),
    "eda_summary": ("processed_df", "preprocessing_signature"),
    "k_metrics": ("scaled_matrix",),
    "recommended_k": ("k_metrics",),
    "selected_k": ("k_metrics",),
    "solver_preferences": (),
    "model": ("scaled_matrix", "selected_k", "solver_preferences"),
    "labels": ("model",),
    "cluster_profiles": ("processed_df", "labels"),
    "run_metadata": ("model",),
    "results": ("cluster_profiles", "run_metadata"),
    "export_payload": ("results",),
}

STATE_SCHEMA: Final[tuple[str, ...]] = tuple(field.name for field in fields(AppState))


def new_app_state() -> AppState:
    """Return an empty state snapshot."""

    return AppState()


def downstream_keys(key: str, *, include_key: bool = False) -> tuple[str, ...]:
    """Return every state key that transitively depends on ``key``.

    The declaration order is retained so resets are deterministic and easy to
    inspect in tests.  ``KeyError`` catches misspelled contract keys at the
    feature boundary instead of silently preserving stale results.
    """

    if key not in STATE_DEPENDENCIES:
        raise KeyError(f"Unknown state key: {key}")

    # ``traversed`` always starts at the changed key.  ``affected`` controls
    # whether the changed value itself is cleared; this distinction lets a
    # solver-preference update retain its new input while invalidating its
    # model-derived descendants.
    traversed = {key}
    affected = {key} if include_key else set()
    changed = True
    while changed:
        changed = False
        for candidate, prerequisites in STATE_DEPENDENCIES.items():
            if candidate not in traversed and any(parent in traversed for parent in prerequisites):
                traversed.add(candidate)
                affected.add(candidate)
                changed = True
    return tuple(name for name in STATE_SCHEMA if name in affected)


def clear_keys(state: AppState, keys: Iterable[str]) -> None:
    """Clear contract keys, rejecting accidental writes outside the schema."""

    for key in keys:
        if key not in STATE_DEPENDENCIES:
            raise KeyError(f"Unknown state key: {key}")
        setattr(state, key, None)


def invalidate_from(state: AppState, key: str, *, include_key: bool = False) -> tuple[str, ...]:
    """Clear artifacts made stale by a change to ``key`` and return their keys."""

    affected = downstream_keys(key, include_key=include_key)
    clear_keys(state, affected)
    return affected


def set_raw_dataset(state: AppState, raw_df: Any, dataset_signature: str) -> None:
    """Atomically replace the validated dataset and clear all derived artifacts."""

    invalidate_from(state, "raw_df", include_key=True)
    state.raw_df = raw_df
    state.dataset_signature = dataset_signature


def set_preprocessed_data(
    state: AppState,
    processed_df: Any,
    scaled_matrix: Any,
    preprocessing_signature: str,
    eda_summary: Any | None = None,
) -> None:
    """Commit TV2 output, replacing every result derived from an older run."""

    if state.raw_df is None or state.dataset_signature is None:
        raise ValueError("A validated dataset is required before preprocessing.")
    invalidate_from(state, "processed_df", include_key=True)
    state.processed_df = processed_df
    state.preprocessing_signature = preprocessing_signature
    state.scaled_matrix = scaled_matrix
    state.eda_summary = eda_summary


def set_k_analysis(state: AppState, k_metrics: Any, recommended_k: int | None) -> None:
    """Commit TV3 analysis and invalidate a prior K selection and model run."""

    if state.scaled_matrix is None:
        raise ValueError("Scaled features are required before K analysis.")
    invalidate_from(state, "k_metrics", include_key=True)
    state.k_metrics = k_metrics
    state.recommended_k = recommended_k


def set_selected_k(state: AppState, selected_k: int) -> None:
    """Confirm K and clear only outputs that require fitting again."""

    if state.k_metrics is None:
        raise ValueError("K analysis is required before selecting K.")
    if selected_k < 2:
        raise ValueError("Selected K must be at least 2.")
    invalidate_from(state, "selected_k", include_key=True)
    state.selected_k = selected_k


def set_solver_preferences(state: AppState, preferences: Any) -> None:
    """Store solver input and invalidate only the solver-derived outputs."""

    invalidate_from(state, "solver_preferences", include_key=False)
    state.solver_preferences = preferences


def set_clustering_result(
    state: AppState,
    model: Any,
    labels: Any,
    cluster_profiles: Any,
    *,
    run_metadata: Any | None = None,
    results: Any | None = None,
) -> None:
    """Atomically commit a successful TV4 run."""

    if state.scaled_matrix is None or state.selected_k is None:
        raise ValueError("Scaled features and a confirmed K are required before clustering.")
    invalidate_from(state, "model", include_key=True)
    state.model = model
    state.labels = labels
    state.cluster_profiles = cluster_profiles
    state.run_metadata = run_metadata
    state.results = results


def set_results(state: AppState, results: Any, export_payload: Any | None = None) -> None:
    """Commit TV6 results only after a valid clustering/profile result exists."""

    if state.cluster_profiles is None:
        raise ValueError("Cluster profiles are required before publishing results.")
    invalidate_from(state, "results", include_key=True)
    state.results = results
    state.export_payload = export_payload
