from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from src.state import new_app_state, set_raw_dataset
from src.validation import (
    CANONICAL_COLUMNS,
    DataValidationError,
    dataset_sha256,
    load_csv_bytes,
    load_sample_dataset,
)


def csv_bytes(data):
    return pd.DataFrame(data).to_csv(index=False).encode("utf-8")


def valid_bytes():
    return csv_bytes({"CustomerID": ["C1", "C2", "C3"], "Recency": [1, 2, None], "Frequency": [3, 4, 5], "Monetary": [10.5, 20, 30]})


def test_signature_uses_original_bytes():
    payload = valid_bytes()
    assert dataset_sha256(payload) == sha256(payload).hexdigest()
    assert dataset_sha256(payload + b"\n") != dataset_sha256(payload)


def test_header_normalization_and_extra_columns():
    payload = csv_bytes({" customerid ": [1, 2], "RECENCY": [3, 4], "frequency ": [5, 6], "Monetary": [7, 8], "Ignored": ["x", "y"]})
    result = load_csv_bytes(payload)
    assert tuple(result.raw_df.columns) == CANONICAL_COLUMNS
    assert "Ignored" not in result.raw_df


@pytest.mark.parametrize(
    "header",
    [
        "CustomerID,CustomerID,Recency,Frequency,Monetary",
        "CustomerID, customerid ,Recency,Frequency,Monetary",
    ],
)
def test_duplicate_canonical_headers_are_rejected(header):
    payload = (header + "\nC1,C1,1,2,3\n").encode()
    with pytest.raises(DataValidationError):
        load_csv_bytes(payload)


def test_customer_id_text_representation_is_preserved():
    result = load_csv_bytes(
        b"CustomerID,Recency,Frequency,Monetary\n0012,1,2,3\n"
    )
    assert result.raw_df.loc[0, "CustomerID"] == "0012"


def test_missing_rfm_is_reported_and_not_imputed():
    result = load_csv_bytes(valid_bytes())
    assert result.quality_report.missing_by_column["Recency"] == 1
    assert pd.isna(result.raw_df.loc[2, "Recency"])


@pytest.mark.parametrize("missing", ["Recency", "CustomerID"])
def test_missing_required_column_is_rejected(missing):
    df = pd.read_csv(BytesIO(valid_bytes())).drop(columns=missing)
    with pytest.raises(DataValidationError, match="Thiếu cột"):
        load_csv_bytes(df.to_csv(index=False).encode())


@pytest.mark.parametrize(("column", "value", "message"), [("Recency", "abc", "không phải số"), ("Frequency", -1, "giá trị âm"), ("Monetary", float("inf"), "vô cực")])
def test_invalid_rfm_domain_is_rejected(column, value, message):
    df = pd.read_csv(BytesIO(valid_bytes()))
    if isinstance(value, str):
        df[column] = df[column].astype(object)
    df.loc[0, column] = value
    with pytest.raises(DataValidationError, match=message):
        load_csv_bytes(df.to_csv(index=False).encode())


def test_missing_or_duplicate_customer_id_is_rejected():
    missing = pd.read_csv(BytesIO(valid_bytes()))
    missing.loc[0, "CustomerID"] = " "
    with pytest.raises(DataValidationError, match="thiếu hoặc rỗng"):
        load_csv_bytes(missing.to_csv(index=False).encode())
    duplicate = pd.read_csv(BytesIO(valid_bytes()))
    duplicate.loc[1, "CustomerID"] = duplicate.loc[0, "CustomerID"]
    with pytest.raises(DataValidationError, match="ánh xạ 1:1"):
        load_csv_bytes(duplicate.to_csv(index=False).encode())


def test_quality_reports_outliers_and_zero_variance():
    payload = csv_bytes({"CustomerID": [f"C{i}" for i in range(6)], "Recency": [1, 1, 1, 1, 1, 100], "Frequency": [2] * 6, "Monetary": [10, 20, 30, 40, 50, 60]})
    report = load_csv_bytes(payload).quality_report
    assert report.iqr_outlier_by_column["Recency"] == 1
    assert report.zero_variance_columns == ("Frequency",)


def test_malformed_and_empty_csv_are_user_facing_errors():
    with pytest.raises(DataValidationError):
        load_csv_bytes(b"")
    with pytest.raises(DataValidationError):
        load_csv_bytes(b'CustomerID,Recency\n"unterminated')


def test_canonical_sample_identity_and_rows():
    sample = Path(__file__).parents[1] / "data" / "sample_customers.csv"
    result = load_sample_dataset(sample)
    assert len(result.raw_df) == 720
    assert result.dataset_signature == "622a6cff9d8b41106268eb1e31e50b5259ccc1d4c318a15a5c496c8edce2a96f"


def test_failed_validation_does_not_mutate_previous_valid_state():
    state = new_app_state()
    valid = load_csv_bytes(valid_bytes())
    set_raw_dataset(state, valid.raw_df, valid.dataset_signature)
    previous_df = state.raw_df
    previous_signature = state.dataset_signature

    with pytest.raises(DataValidationError):
        load_csv_bytes(b"CustomerID,Recency,Frequency,Monetary\nC1,bad,2,3\n")

    assert state.raw_df is previous_df
    assert state.dataset_signature == previous_signature
