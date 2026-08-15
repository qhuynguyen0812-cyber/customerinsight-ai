import pytest
import pandas as pd
import numpy as np
from src.clustering import analyze_candidate_k, recommend_k, get_default_solver_kwargs

@pytest.fixture
def dummy_scaled_data():
    # Tạo mock data mô phỏng 3 cụm rõ rệt để test mà không hard-code input thực
    np.random.seed(42)
    cluster_1 = np.random.normal(0, 0.1, (50, 3))
    cluster_2 = np.random.normal(5, 0.1, (50, 3))
    cluster_3 = np.random.normal(10, 0.1, (50, 3))
    data = np.vstack([cluster_1, cluster_2, cluster_3])
    return pd.DataFrame(data, columns=['Recency', 'Frequency', 'Monetary'])

def test_analyze_candidate_k_structure(dummy_scaled_data):
    results = analyze_candidate_k(dummy_scaled_data, k_min=2, k_max=4)
    assert 'k' in results
    assert 'inertia' in results
    assert 'silhouette' in results
    assert results['k'] == [2, 3, 4]
    assert len(results['inertia']) == 3
    assert len(results['silhouette']) == 3

def test_recommend_k_logic(dummy_scaled_data):
    results = analyze_candidate_k(dummy_scaled_data, k_min=2, k_max=5)
    rec_k = recommend_k(results)
    # Vì data có 3 cụm rõ ràng, rec_k phải tính ra 3 một cách tự nhiên (computed, không hard-code)
    assert rec_k == 3

def test_solver_kwargs_defaults():
    defaults = get_default_solver_kwargs()
    assert defaults['init'] == 'k-means++'
    assert defaults['n_init'] == 10
    assert defaults['random_state'] == 42