import pytest
import pandas as pd
import numpy as np
from src.clustering import analyze_candidate_k, recommend_k, run_kmeans

@pytest.fixture
def dummy_small_data():
    """Tạo bộ dữ liệu siêu nhỏ (10 dòng) để test lỗi 'too few samples'."""
    np.random.seed(42)
    data = np.random.normal(0, 1, (10, 3))
    return pd.DataFrame(data, columns=['R', 'F', 'M'])

def test_analyze_k_invalid_range(dummy_small_data):
    # k_min >= k_max
    with pytest.raises(ValueError, match="k_min phải nhỏ hơn k_max"):
        analyze_candidate_k(dummy_small_data, k_min=5, k_max=3)

def test_analyze_k_too_few_samples(dummy_small_data):
    # k_max vượt quá số lượng mẫu (10)
    with pytest.raises(ValueError, match="không được lớn hơn hoặc bằng tổng số lượng mẫu"):
        analyze_candidate_k(dummy_small_data, k_min=2, k_max=15)

def test_run_kmeans_invalid_k(dummy_small_data):
    # k < 2
    with pytest.raises(ValueError, match="lớn hơn hoặc bằng 2"):
        run_kmeans(dummy_small_data, k=1)

def test_run_kmeans_too_few_samples(dummy_small_data):
    # k >= n_samples (10)
    with pytest.raises(ValueError, match="nhỏ hơn tổng số lượng mẫu"):
        run_kmeans(dummy_small_data, k=10)