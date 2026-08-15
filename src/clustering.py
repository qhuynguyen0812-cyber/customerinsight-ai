"""Canonical K analysis and K-Means fit engine owned by TV3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Iterator, Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

DEFAULT_SOLVER_KWARGS: Final[dict[str, Any]] = {
    "init": "k-means++",
    "n_init": 10,
    "random_state": 42,
    "max_iter": 300,
    "tol": 0.0001,
}
SUPPORTED_SOLVER_KWARGS: Final[frozenset[str]] = frozenset(DEFAULT_SOLVER_KWARGS)


@dataclass(frozen=True)
class KMeansResult:
    """Artifacts required by downstream clustering/profile orchestration."""

    model: KMeans
    labels: NDArray[np.int_]
    inertia: float
    iterations: int

    def __iter__(self) -> Iterator[Any]:
        """Preserve the former ``model, labels = run_kmeans(...)`` usage."""

        yield self.model
        yield self.labels


def get_default_solver_kwargs() -> dict[str, Any]:
    """Return a fresh copy of the explicit Phase 1 solver defaults."""

    return DEFAULT_SOLVER_KWARGS.copy()


def _solver_kwargs(overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    effective = get_default_solver_kwargs()
    if overrides is None:
        return effective
    unknown = set(overrides) - SUPPORTED_SOLVER_KWARGS
    if unknown:
        raise ValueError("Unsupported solver setting(s): " + ", ".join(sorted(unknown)))
    effective.update(overrides)
    return effective


def _matrix(X_scaled: ArrayLike) -> NDArray[np.float64]:
    try:
        matrix = np.asarray(X_scaled, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("X_scaled must be a numeric 2D matrix.") from exc
    if matrix.ndim != 2:
        raise ValueError("X_scaled must be a 2D matrix.")
    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("X_scaled must contain at least one row and one feature.")
    if not np.isfinite(matrix).all():
        raise ValueError("X_scaled must contain only finite values.")
    return matrix


def _validate_fit_k(k: int, n_samples: int) -> None:
    if isinstance(k, bool) or not isinstance(k, (int, np.integer)):
        raise ValueError("K must be an integer.")
    if k < 2:
        raise ValueError("K must be at least 2.")
    if k > n_samples:
        raise ValueError(f"K must not exceed the number of samples ({n_samples}).")


def run_kmeans(
    X_scaled: ArrayLike,
    k: int,
    solver_kwargs: Mapping[str, Any] | None = None,
) -> KMeansResult:
    """Fit deterministic K-Means directly on TV2's canonical scaled matrix."""

    matrix = _matrix(X_scaled)
    _validate_fit_k(k, len(matrix))
    model = KMeans(n_clusters=int(k), **_solver_kwargs(solver_kwargs))
    labels = model.fit_predict(matrix)
    return KMeansResult(
        model=model,
        labels=labels,
        inertia=float(model.inertia_),
        iterations=int(model.n_iter_),
    )


def analyze_candidate_k(
    X_scaled: ArrayLike,
    k_min: int = 2,
    k_max: int = 10,
    solver_kwargs: Mapping[str, Any] | None = None,
) -> dict[str, list[int] | list[float]]:
    """Compute inertia and silhouette for every K in the inclusive range.

    Silhouette requires ``2 <= K < n_samples``; the whole request is validated
    before any model is fitted so callers can commit the result transactionally.
    """

    matrix = _matrix(X_scaled)
    if isinstance(k_min, bool) or not isinstance(k_min, (int, np.integer)):
        raise ValueError("k_min must be an integer.")
    if isinstance(k_max, bool) or not isinstance(k_max, (int, np.integer)):
        raise ValueError("k_max must be an integer.")
    if k_min < 2:
        raise ValueError("k_min must be at least 2.")
    if k_max < k_min:
        raise ValueError("k_max must be greater than or equal to k_min.")
    if k_max >= len(matrix):
        raise ValueError(
            f"k_max must be less than the number of samples ({len(matrix)}) "
            "because silhouette is undefined when K >= n_samples."
        )

    results: dict[str, list[int] | list[float]] = {
        "k": [],
        "inertia": [],
        "silhouette": [],
    }
    for k in range(int(k_min), int(k_max) + 1):
        fit = run_kmeans(matrix, k, solver_kwargs)
        results["k"].append(k)
        results["inertia"].append(fit.inertia)
        results["silhouette"].append(float(silhouette_score(matrix, fit.labels)))
    return results


def recommend_k(analysis_results: Mapping[str, list[int] | list[float]]) -> int:
    """Recommend the smallest K attaining the computed maximum silhouette."""

    try:
        candidates = list(analysis_results["k"])
        silhouettes = list(analysis_results["silhouette"])
    except (KeyError, TypeError) as exc:
        raise ValueError("Analysis must contain k and silhouette metrics.") from exc
    if not candidates or len(candidates) != len(silhouettes):
        raise ValueError("Analysis k and silhouette metrics must be non-empty and aligned.")
    if any(not np.isfinite(score) for score in silhouettes):
        raise ValueError("Silhouette metrics must be finite.")
    return int(min(zip(candidates, silhouettes), key=lambda item: (-item[1], item[0]))[0])
