"""CSV loading and validation for the canonical CustomerInsight RFM input."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError, ParserError

CANONICAL_COLUMNS: Final[tuple[str, ...]] = (
    "CustomerID", "Recency", "Frequency", "Monetary"
)
RFM_COLUMNS: Final[tuple[str, ...]] = ("Recency", "Frequency", "Monetary")
_HEADER_LOOKUP: Final[dict[str, str]] = {
    name.casefold(): name for name in CANONICAL_COLUMNS
}


class DataValidationError(ValueError):
    """An expected, user-correctable CSV validation failure."""


@dataclass(frozen=True)
class DataQualityReport:
    """Quality measurements calculated before imputation or clipping."""

    row_count: int
    missing_by_column: dict[str, int]
    duplicate_row_count: int
    duplicate_customer_id_count: int
    non_numeric_by_column: dict[str, int]
    negative_by_column: dict[str, int]
    infinity_by_column: dict[str, int]
    iqr_outlier_by_column: dict[str, int]
    zero_variance_columns: tuple[str, ...]


@dataclass(frozen=True)
class ValidatedDataset:
    raw_df: pd.DataFrame
    dataset_signature: str
    quality_report: DataQualityReport


def dataset_sha256(file_bytes: bytes) -> str:
    """Return the deterministic SHA-256 of the original file bytes."""

    if not isinstance(file_bytes, bytes):
        raise TypeError("file_bytes must be bytes")
    return sha256(file_bytes).hexdigest()


def _canonical_column_mapping(columns: pd.Index) -> dict[object, str]:
    mapping: dict[object, str] = {}
    matched: dict[str, object] = {}
    for original in columns:
        canonical = _HEADER_LOOKUP.get(str(original).strip().casefold())
        if canonical is None:
            continue
        if canonical in matched:
            raise DataValidationError(
                f"Cột {canonical} xuất hiện nhiều lần sau khi chuẩn hóa tiêu đề."
            )
        matched[canonical] = original
        mapping[original] = canonical
    missing = [name for name in CANONICAL_COLUMNS if name not in matched]
    if missing:
        raise DataValidationError("Thiếu cột bắt buộc: " + ", ".join(missing) + ".")
    return mapping


def _iqr_outlier_count(series: pd.Series) -> int:
    values = series.dropna()
    if values.empty:
        return 0
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    return int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())


def validate_dataframe(df: pd.DataFrame, file_bytes: bytes) -> ValidatedDataset:
    """Validate data and return raw canonical columns without preprocessing."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if df.empty:
        raise DataValidationError("CSV không có dòng dữ liệu nào.")

    mapping = _canonical_column_mapping(df.columns)
    raw_df = df.rename(columns=mapping).loc[:, list(CANONICAL_COLUMNS)].copy()
    customer_ids = raw_df["CustomerID"]
    missing_ids = customer_ids.isna() | customer_ids.astype("string").str.strip().eq("")
    if missing_ids.any():
        raise DataValidationError(
            f"CustomerID có {int(missing_ids.sum())} giá trị thiếu hoặc rỗng."
        )

    duplicate_rows = int(raw_df.duplicated().sum())
    duplicate_ids = int(customer_ids.duplicated(keep=False).sum())
    if duplicate_ids:
        raise DataValidationError(
            f"CustomerID có {duplicate_ids} dòng trùng; v1 yêu cầu ánh xạ 1:1."
        )

    non_numeric: dict[str, int] = {}
    negative: dict[str, int] = {}
    infinity: dict[str, int] = {}
    for column in RFM_COLUMNS:
        original = raw_df[column]
        converted = pd.to_numeric(original, errors="coerce")
        non_numeric[column] = int((original.notna() & converted.isna()).sum())
        if non_numeric[column]:
            raise DataValidationError(
                f"Cột {column} có {non_numeric[column]} giá trị không phải số."
            )
        infinity[column] = int(np.isinf(converted.dropna().to_numpy()).sum())
        if infinity[column]:
            raise DataValidationError(
                f"Cột {column} có {infinity[column]} giá trị vô cực."
            )
        negative[column] = int((converted.dropna() < 0).sum())
        if negative[column]:
            raise DataValidationError(
                f"Cột {column} có {negative[column]} giá trị âm."
            )
        raw_df[column] = converted

    quality = DataQualityReport(
        row_count=len(raw_df),
        missing_by_column={name: int(raw_df[name].isna().sum()) for name in CANONICAL_COLUMNS},
        duplicate_row_count=duplicate_rows,
        duplicate_customer_id_count=duplicate_ids,
        non_numeric_by_column=non_numeric,
        negative_by_column=negative,
        infinity_by_column=infinity,
        iqr_outlier_by_column={name: _iqr_outlier_count(raw_df[name]) for name in RFM_COLUMNS},
        zero_variance_columns=tuple(
            name for name in RFM_COLUMNS if raw_df[name].dropna().nunique() <= 1
        ),
    )
    return ValidatedDataset(raw_df, dataset_sha256(file_bytes), quality)


def load_csv_bytes(file_bytes: bytes) -> ValidatedDataset:
    """Parse and validate CSV bytes locally without any external upload."""

    if not isinstance(file_bytes, bytes):
        raise TypeError("file_bytes must be bytes")
    if not file_bytes:
        raise DataValidationError("Tệp CSV đang trống.")
    try:
        df = pd.read_csv(BytesIO(file_bytes))
    except (EmptyDataError, ParserError, UnicodeDecodeError) as exc:
        raise DataValidationError("Không thể đọc tệp CSV hợp lệ.") from exc
    return validate_dataframe(df, file_bytes)


def load_sample_dataset(path: str | Path) -> ValidatedDataset:
    """Load the canonical sample from a project-controlled local path."""

    try:
        file_bytes = Path(path).read_bytes()
    except OSError as exc:
        raise DataValidationError("Không thể đọc dataset mẫu.") from exc
    return load_csv_bytes(file_bytes)
