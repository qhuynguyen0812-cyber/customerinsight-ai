"""Local preprocessing for the canonical CustomerID/RFM dataset."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Final, Sequence

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

RFM_FEATURES: Final[tuple[str, ...]] = ("Recency", "Frequency", "Monetary")
REQUIRED_COLUMNS: Final[tuple[str, ...]] = ("CustomerID", *RFM_FEATURES)
DEFAULT_MISSING_STRATEGY: Final[str] = "median"
DEFAULT_OUTLIER_STRATEGY: Final[str] = "iqr_clip"


class PreprocessingError(ValueError):
    """An expected, user-correctable preprocessing failure."""


def _validate_input(df: pd.DataFrame) -> None:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise PreprocessingError("Missing required columns: " + ", ".join(missing))
    if df.empty:
        raise PreprocessingError("The dataset must contain at least one row.")
    for column in RFM_FEATURES:
        values = pd.to_numeric(df[column], errors="coerce")
        invalid = df[column].notna() & values.isna()
        if invalid.any():
            raise PreprocessingError(f"{column} contains non-numeric values.")
        if np.isinf(values.dropna().to_numpy(dtype=float)).any():
            raise PreprocessingError(f"{column} contains infinite values.")


def check_data_quality(df: pd.DataFrame) -> dict[str, Any]:
    """Return a compact quality report without changing the input."""

    total_rows = len(df)
    missing = df.isna().sum()
    percentages = (
        (missing / total_rows * 100).round(2) if total_rows else missing.astype(float)
    )
    return {
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "missing_counts": {key: int(value) for key, value in missing.items()},
        "missing_percentages": percentages.to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def handle_missing_values(
    df: pd.DataFrame, strategy: str = DEFAULT_MISSING_STRATEGY
) -> pd.DataFrame:
    """Impute each RFM feature independently while preserving all rows and IDs."""

    if strategy != DEFAULT_MISSING_STRATEGY:
        raise PreprocessingError(
            f"Unsupported missing strategy: {strategy!r}. Supported: 'median'."
        )
    _validate_input(df)
    result = df.copy(deep=True)
    for column in RFM_FEATURES:
        values = pd.to_numeric(result[column], errors="coerce")
        median = values.median(skipna=True)
        if pd.isna(median):
            raise PreprocessingError(
                f"{column} cannot be imputed because it has no valid values."
            )
        result[column] = values.fillna(median)
    return result


def handle_outliers_iqr(
    df: pd.DataFrame,
    columns: Sequence[str] | None = None,
    factor: float = 1.5,
) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    """Clip selected features to deterministic Tukey IQR bounds."""

    selected = tuple(columns) if columns is not None else RFM_FEATURES
    unknown = [column for column in selected if column not in df.columns]
    if unknown:
        raise PreprocessingError("Missing clipping columns: " + ", ".join(unknown))
    if not np.isfinite(factor) or factor < 0:
        raise PreprocessingError("IQR factor must be a finite non-negative number.")

    result = df.copy(deep=True)
    bounds: dict[str, dict[str, float]] = {}
    for column in selected:
        values = pd.to_numeric(result[column], errors="coerce")
        if values.isna().any() or np.isinf(values.to_numpy(dtype=float)).any():
            raise PreprocessingError(
                f"{column} must be finite and complete before IQR clipping."
            )
        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        bounds[column] = {
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_bound": lower,
            "upper_bound": upper,
        }
        result[column] = values.clip(lower=lower, upper=upper)
    return result, bounds


def scale_rfm_features(
    df: pd.DataFrame, feature_cols: Sequence[str] | None = None
) -> tuple[np.ndarray, StandardScaler, pd.DataFrame]:
    """Fit StandardScaler on exactly the three canonical RFM features."""

    selected = tuple(feature_cols) if feature_cols is not None else RFM_FEATURES
    if selected != RFM_FEATURES:
        raise PreprocessingError(
            "Scaler features must be exactly Recency, Frequency, Monetary."
        )
    values = df.loc[:, list(RFM_FEATURES)].astype(float)
    if not np.isfinite(values.to_numpy()).all():
        raise PreprocessingError("RFM values must be finite and complete before scaling.")
    scaler = StandardScaler()
    scaled_matrix = scaler.fit_transform(values)
    scaled_df = pd.DataFrame(scaled_matrix, columns=RFM_FEATURES, index=df.index)
    return scaled_matrix, scaler, scaled_df


def _stable_number(value: float) -> str:
    return float(value).hex()


def _signature(metadata: dict[str, Any]) -> str:
    payload = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def run_pipeline_preprocessing(
    df_raw: pd.DataFrame,
    missing_strategy: str = DEFAULT_MISSING_STRATEGY,
    outlier_strategy: str = DEFAULT_OUTLIER_STRATEGY,
) -> dict[str, Any]:
    """Run median imputation, IQR clipping, and RFM-only scaling locally."""

    if outlier_strategy != DEFAULT_OUTLIER_STRATEGY:
        raise PreprocessingError(
            f"Unsupported outlier strategy: {outlier_strategy!r}. Supported: 'iqr_clip'."
        )
    _validate_input(df_raw)
    quality_report = check_data_quality(df_raw)
    imputed = handle_missing_values(df_raw, missing_strategy)
    medians = {column: float(imputed[column].median()) for column in RFM_FEATURES}
    processed_df, iqr_bounds = handle_outliers_iqr(imputed)
    scaled_matrix, scaler, scaled_df = scale_rfm_features(processed_df)

    metadata = {
        "missing_strategy": missing_strategy,
        "outlier_strategy": outlier_strategy,
        "features": list(RFM_FEATURES),
        "medians": {key: _stable_number(value) for key, value in medians.items()},
        "iqr_bounds": {
            column: {key: _stable_number(value) for key, value in values.items()}
            for column, values in iqr_bounds.items()
        },
    }
    signature = _signature(metadata)
    return {
        "processed_df": processed_df,
        "scaled_matrix": scaled_matrix,
        "scaler": scaler,
        "scaled_df": scaled_df,
        "quality_report": quality_report,
        "iqr_bounds": iqr_bounds,
        "metadata": metadata,
        "preprocessing_signature": signature,
        "eda_summary": {
            "quality_report": quality_report,
            "iqr_bounds": iqr_bounds,
            "metadata": metadata,
            "scaler": scaler,
        },
    }


# Backward-compatible descriptive alias for callers preferring a shorter name.
preprocess_rfm = run_pipeline_preprocessing
