"""TV3-owned K analysis / fit-engine scaffold. No implementation in team baseline."""
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def get_default_solver_kwargs() -> dict:
    """Trả về cấu hình mặc định của thuật toán theo đúng tài liệu khóa."""
    return {
        'init': 'k-means++',
        'n_init': 10,
        'random_state': 42,
        'max_iter': 300,
        'tol': 0.0001
    }

def analyze_candidate_k(df_scaled: pd.DataFrame, k_min: int = 2, k_max: int = 10, solver_kwargs: dict = None) -> dict:
    """
    FR-009: Phân tích candidate K.
    Tính toán Inertia và Silhouette cho từng K trong khoảng k_min đến k_max.
    """
    if solver_kwargs is None:
        solver_kwargs = get_default_solver_kwargs()
        
    results = {'k': [], 'inertia': [], 'silhouette': []}
    
    for k in range(k_min, k_max + 1):
        kmeans = KMeans(n_clusters=k, **solver_kwargs)
        labels = kmeans.fit_predict(df_scaled)
        
        results['k'].append(k)
        results['inertia'].append(kmeans.inertia_)
        results['silhouette'].append(silhouette_score(df_scaled, labels))
        
    return results

def recommend_k(analysis_results: dict) -> int:
    """
    Gợi ý giá trị K tối ưu dựa trên max Silhouette.
    Không được hard-code K=3.
    """
    silhouettes = analysis_results['silhouette']
    max_idx = silhouettes.index(max(silhouettes))
    return analysis_results['k'][max_idx]

def run_kmeans(df_scaled: pd.DataFrame, k: int, solver_kwargs: dict = None):
    """
    API contract handoff cho TV4.
    FR-011: Chạy K-Means execution.
    """
    if solver_kwargs is None:
        solver_kwargs = get_default_solver_kwargs()
        
    kmeans = KMeans(n_clusters=k, **solver_kwargs)
    labels = kmeans.fit_predict(df_scaled)
    
    return kmeans, labels