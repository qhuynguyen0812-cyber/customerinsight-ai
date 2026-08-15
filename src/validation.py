"""CSV loading and validation for the canonical CustomerInsight RFM input."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError, ParserError

CANONICAL_COLUMNS: Final[tuple[str, ...]] = (
    "CustomerID",
    "Recency",
    "Frequency",
    "Monetary",
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
    values = series.replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        return 0
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    return int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())


def build_quality_report(raw_df: pd.DataFrame) -> DataQualityReport:
    """Measure canonical data without modifying, imputing, or clipping it."""

    missing = {
        name: int(raw_df[name].isna().sum()) for name in CANONICAL_COLUMNS
    }
    non_numeric: dict[str, int] = {}
    negative: dict[str, int] = {}
    infinity: dict[str, int] = {}
    numeric_columns: dict[str, pd.Series] = {}
    for column in RFM_COLUMNS:
        original = raw_df[column]
        converted = pd.to_numeric(original, errors="coerce")
        numeric_columns[column] = converted
        non_numeric[column] = int((original.notna() & converted.isna()).sum())
        infinity[column] = int(np.isinf(converted.dropna().to_numpy()).sum())
        negative[column] = int((converted.dropna() < 0).sum())

    customer_ids = raw_df["CustomerID"]
    return DataQualityReport(
        row_count=len(raw_df),
        missing_by_column=missing,
        duplicate_row_count=int(raw_df.duplicated().sum()),
        duplicate_customer_id_count=int(customer_ids.duplicated(keep=False).sum()),
        non_numeric_by_column=non_numeric,
        negative_by_column=negative,
        infinity_by_column=infinity,
        iqr_outlier_by_column={
            name: _iqr_outlier_count(numeric_columns[name]) for name in RFM_COLUMNS
        },
        zero_variance_columns=tuple(
            name
            for name in RFM_COLUMNS
            if numeric_columns[name].dropna().nunique() <= 1
        ),
    )


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

    duplicate_ids = int(customer_ids.duplicated(keep=False).sum())
    if duplicate_ids:
        raise DataValidationError(
            f"CustomerID có {duplicate_ids} dòng trùng; TV1 yêu cầu ánh xạ 1:1."
        )

    quality = build_quality_report(raw_df)
    for column in RFM_COLUMNS:
        if quality.non_numeric_by_column[column]:
            raise DataValidationError(
                f"Cột {column} có {quality.non_numeric_by_column[column]} "
                "giá trị không phải số."
            )
        if quality.infinity_by_column[column]:
            raise DataValidationError(
                f"Cột {column} có {quality.infinity_by_column[column]} giá trị vô cực."
            )
        if quality.negative_by_column[column]:
            raise DataValidationError(
                f"Cột {column} có {quality.negative_by_column[column]} giá trị âm."
            )
        raw_df[column] = pd.to_numeric(raw_df[column], errors="coerce")

    return ValidatedDataset(
        raw_df,
        dataset_sha256(file_bytes),
        build_quality_report(raw_df),
    )


def load_csv_bytes(file_bytes: bytes) -> ValidatedDataset:
    """Parse and validate CSV bytes locally without any external upload."""

    if not isinstance(file_bytes, bytes):
        raise TypeError("file_bytes must be bytes")
    if not file_bytes:
        raise DataValidationError("Tệp CSV đang trống.")
    try:
        text = file_bytes.decode("utf-8-sig")
        header = next(csv.reader(StringIO(text), strict=True))
        _canonical_column_mapping(pd.Index(header))
        # Object dtype preserves identifiers such as "0012" exactly as supplied.
        df = pd.read_csv(BytesIO(file_bytes), dtype=object)
    except (EmptyDataError, ParserError, UnicodeDecodeError, csv.Error, StopIteration) as exc:
        raise DataValidationError("Không thể đọc tệp CSV hợp lệ.") from exc
    return validate_dataframe(df, file_bytes)


def load_sample_dataset(path: str | Path) -> ValidatedDataset:
    """Load the canonical sample through the same byte-validation pipeline."""

    try:
        file_bytes = Path(path).read_bytes()
    except OSError as exc:
        raise DataValidationError("Không thể đọc dataset mẫu.") from exc
    return load_csv_bytes(file_bytes)
