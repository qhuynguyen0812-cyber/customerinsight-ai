"""
Module thực hiện phân cụm K-Means cho RFM data theo đúng contract.
"""
from typing import Tuple
import pandas as pd
from sklearn.cluster import KMeans

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
    Huấn luyện K-Means với kiểm tra ràng buộc đầu vào.
    """
    if scaled_df is None or scaled_df.empty:
        raise ValueError("Dữ liệu đầu vào không được để trống.")

    if k < 2:
        raise ValueError(f"Số lượng cụm k phải >= 2, giá trị nhận được: {k}")

    if len(scaled_df) < k:
        raise ValueError(f"Số lượng mẫu ({len(scaled_df)}) phải lớn hơn hoặc bằng số cụm k ({k}).")

    missing_cols = [col for col in FEATURE_COLS if col not in scaled_df.columns]
    if missing_cols:
        raise KeyError(f"Thiếu các cột bắt buộc trong dữ liệu: {missing_cols}")

    features = scaled_df[FEATURE_COLS]

    if features.isnull().any().any():
        raise ValueError("Dữ liệu chứa giá trị null/NaN trước khi đưa vào K-Means.")

    model = KMeans(
        n_clusters=k,
        init=KMEANS_INIT,
        n_init=KMEANS_N_INIT,
        random_state=KMEANS_RANDOM_STATE,
        max_iter=KMEANS_MAX_ITER,
        tol=KMEANS_TOL
    )

    labels = model.fit_predict(features)

    cluster_labels = pd.Series(
        labels, 
        index=scaled_df.index, 
        name="Cluster"
    )
    
    return model, cluster_labels