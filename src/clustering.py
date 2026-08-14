"""
Module thực hiện phân cụm K-Means cho RFM data theo đúng contract.
"""
from typing import Tuple
import pandas as pd
from sklearn.cluster import KMeans

# Các tham số cố định bắt buộc theo quy định
KMEANS_INIT = "k-means++"
KMEANS_N_INIT = 10
KMEANS_RANDOM_STATE = 42
KMEANS_MAX_ITER = 300
KMEANS_TOL = 0.0001
FEATURE_COLS = ["Recency", "Frequency", "Monetary"]



def run_kmeans(
    scaled_df: pd.DataFrame, 
    k: int
) -> Tuple[KMeans, pd.Series]:
    """
    Huấn luyện K-Means và trả về model cùng nhãn cụm (Cluster ID).

    Parameters:
    ----------
    scaled_df : pd.DataFrame
        DataFrame chứa các features đã được chuẩn hóa (StandardScaler).
    k : int
        Số lượng cụm do bước phân tích K (TV3) truyền sang.

    Returns:
    -------
    Tuple[KMeans, pd.Series]
        - model: Đối tượng KMeans đã fit.
        - cluster_labels: Series chứa nhãn cụm [0, k-1] với index tương ứng.
    """
    # 1. Đảm bảo dữ liệu đầu vào chỉ chứa 3 cột RFM
    features = scaled_df[FEATURE_COLS]

    # 2. Khởi tạo mô hình theo đúng bộ tham số khóa cứng
    model = KMeans(
        n_clusters=k,
        init=KMEANS_INIT,
        n_init=KMEANS_N_INIT,
        random_state=KMEANS_RANDOM_STATE,
        max_iter=KMEANS_MAX_ITER,
        tol=KMEANS_TOL
    )

    # 3. Fit và dự đoán nhãn cụm
    labels = model.fit_predict(features)

    # 4. Trả về model và nhãn dạng Series
    cluster_labels = pd.Series(
        labels, 
        index=scaled_df.index, 
        name="Cluster"
    )
    
    return model, cluster_labels