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
    Hardening Phase 2: Bắt lỗi ngoại lệ K-range và số lượng mẫu.
    """
    n_samples = len(df_scaled)
    
    # P2-G04: Bắt các trường hợp ngoại lệ
    if k_min < 2:
        raise ValueError("k_min phải lớn hơn hoặc bằng 2.")
    if k_min >= k_max:
        raise ValueError("k_min phải nhỏ hơn k_max.")
    if k_max >= n_samples:
        raise ValueError(f"k_max ({k_max}) không được lớn hơn hoặc bằng tổng số lượng mẫu ({n_samples}).")

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
    FR-010: Gợi ý giá trị K tối ưu dựa trên max Silhouette.
    Không hard-code K=3.
    """
    if not analysis_results or 'silhouette' not in analysis_results or not analysis_results['silhouette']:
        raise ValueError("Kết quả phân tích không hợp lệ hoặc trống.")
        
    silhouettes = analysis_results['silhouette']
    max_idx = silhouettes.index(max(silhouettes))
    return analysis_results['k'][max_idx]

def run_kmeans(df_scaled: pd.DataFrame, k: int, solver_kwargs: dict = None):
    """
    FR-011: Chạy K-Means execution (API contract cho TV4).
    Hardening Phase 2: Bắt lỗi invalid K trước khi fit model.
    """
    n_samples = len(df_scaled)
    
    # P2-G04: Bắt lỗi K không hợp lệ
    if k < 2:
        raise ValueError("Số cụm K được chọn phải lớn hơn hoặc bằng 2.")
    if k >= n_samples:
        raise ValueError(f"Số cụm K ({k}) phải nhỏ hơn tổng số lượng mẫu ({n_samples}).")

    if solver_kwargs is None:
        solver_kwargs = get_default_solver_kwargs()
        
    kmeans = KMeans(n_clusters=k, **solver_kwargs)
    labels = kmeans.fit_predict(df_scaled)
    
    return kmeans, labels