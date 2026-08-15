"""TV4 RFM profile contract tests."""

import numpy as np
import pandas as pd
import pytest

from components.results_export import PROFILE_REQUIRED_COLUMNS, validate_profile
from src.profiling import compute_cluster_profiles, generate_business_interpretation


@pytest.fixture
def customers() -> pd.DataFrame:
    return pd.DataFrame({
        "CustomerID": ["A", "B", "C", "D"],
        "Recency": [1.0, 3.0, 20.0, 30.0],
        "Frequency": [10.0, 6.0, 2.0, 1.0],
        "Monetary": [100.0, 60.0, 20.0, 10.0],
    })


def test_module_import_and_invalid_inputs(customers) -> None:
    import src.profiling
    assert src.profiling is not None
    with pytest.raises(ValueError, match="non-empty"):
        compute_cluster_profiles(customers.iloc[0:0], [])
    with pytest.raises(ValueError, match="match all 4"):
        compute_cluster_profiles(customers, [0, 1])


def test_profiles_use_business_values_and_have_exact_counts(customers) -> None:
    profile = compute_cluster_profiles(customers, np.array([7, 7, 2, 2]))
    assert profile["Cluster"].tolist() == [2, 7]
    assert profile["count"].sum() == len(customers)
    assert profile.set_index("Cluster").loc[7, "mean Recency"] == pytest.approx(2.0)
    assert profile.set_index("Cluster").loc[7, "mean Frequency"] == pytest.approx(8.0)
    assert profile.set_index("Cluster").loc[7, "mean Monetary"] == pytest.approx(80.0)
    assert not (profile[["mean Recency", "mean Frequency", "mean Monetary"]].abs() < 3).all().all()


def test_profile_matches_tv6_and_every_cluster_has_a_name(customers) -> None:
    profile = compute_cluster_profiles(customers, [0, 0, 1, 1])
    assert all(column in profile.columns for column in PROFILE_REQUIRED_COLUMNS)
    assert validate_profile(profile).equals(profile)
    assert profile["SegmentName"].notna().all()
    assert profile["SegmentName"].str.strip().ne("").all()


def test_names_follow_statistics_not_raw_cluster_id(customers) -> None:
    first = compute_cluster_profiles(customers, [0, 0, 1, 1])
    swapped = compute_cluster_profiles(customers, [9, 9, 4, 4])
    assert first.loc[first["mean Monetary"].idxmax(), "SegmentName"] == swapped.loc[
        swapped["mean Monetary"].idxmax(), "SegmentName"
    ]


@pytest.mark.parametrize("labels", [[0, 1, 2, 3], [0, 0, 1, 2]])
def test_dynamic_k_and_interpretation_are_deterministic(customers, labels) -> None:
    profile = compute_cluster_profiles(customers, labels)
    first = generate_business_interpretation(profile)
    second = generate_business_interpretation(profile.copy())
    assert first == second
    assert set(first) == set(labels)
    assert all(item["segment_name"].strip() for item in first.values())
    assert all("churn" not in item["segment_name"].lower() for item in first.values())
