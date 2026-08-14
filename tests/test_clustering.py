import numpy as np
import pandas as pd
import pytest
from src.clustering import run_kmeans
from src.profiling import compute_cluster_profiles, generate_business_interpretation


@pytest.fixture
def sample_rfm_data():
    """Tạo dữ liệu mẫu gồm 12 khách hàng với các đặc trưng RFM."""
    np.random.seed(42)
    data = {
        "Recency": [10, 15, 12, 100, 120, 110, 5, 8, 9, 200, 210, 205],
        "Frequency": [15, 18, 14, 2, 1, 2, 20, 22, 19, 1, 1, 1],
        "Monetary": [500, 600, 550, 50, 40, 45, 800, 950, 890, 20, 30, 25],
    }
    return pd.DataFrame(data)


def test_run_kmeans_output_structure(sample_rfm_data):
    """Kiểm tra số lượng nhãn và số cụm trả về từ mô hình."""
    k = 3
    model, labels = run_kmeans(sample_rfm_data, k=k)

    assert len(labels) == len(sample_rfm_data)
    assert len(np.unique(labels)) == k
    assert model.n_clusters == k


def test_compute_cluster_profiles(sample_rfm_data):
    """Kiểm tra bảng thống kê đặc trưng của các cụm."""
    k = 3
    _, labels = run_kmeans(sample_rfm_data, k=k)
    profile_df = compute_cluster_profiles(sample_rfm_data, labels)

    expected_cols = [
        "Cluster",
        "Count",
        "Percentage",
        "Recency_Mean",
        "Recency_Median",
        "Frequency_Mean",
        "Frequency_Median",
        "Monetary_Mean",
        "Monetary_Median",
    ]

    for col in expected_cols:
        assert col in profile_df.columns

    assert profile_df["Count"].sum() == len(sample_rfm_data)
    assert pytest.approx(profile_df["Percentage"].sum(), 0.1) == 100.0

 

def test_generate_business_interpretation(sample_rfm_data):
    """Kiểm tra việc sinh diễn giải kinh doanh mà không phụ thuộc hard-code k=3."""
    for test_k in [2, 4]:
        _, labels = run_kmeans(sample_rfm_data, k=test_k)
        profile_df = compute_cluster_profiles(sample_rfm_data, labels)
        interpretations = generate_business_interpretation(profile_df)

        assert len(interpretations) == test_k
        for c_id in range(test_k):
            assert c_id in interpretations
            assert "segment_name" in interpretations[c_id]
            assert "characteristics" in interpretations[c_id]
            assert "recommendation" in interpretations[c_id]