feature/tv2-preprocessing-eda
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict, Any

def check_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    FR-004: Data Quality Assessment
    Trả về báo cáo chất lượng dữ liệu bao gồm missing values và số lượng bản ghi.
    """
    total_rows = len(df)
    missing_report = df.isnull().sum().to_dict()
    missing_pct = (df.isnull().sum() / total_rows * 100).round(2).to_dict()
    
    return {
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "missing_counts": missing_report,
        "missing_percentages": missing_pct,
        "duplicate_rows": int(df.duplicated().sum())
    }

def handle_missing_values(df: pd.DataFrame, strategy: str = "median") -> pd.DataFrame:
    """
    FR-005: Missing values handling
    Default: median imputation.
    """
    df_clean = df.copy()
    rfm_cols = ['Recency', 'Frequency', 'Monetary']
    
    for col in rfm_cols:
        if col in df_clean.columns and df_clean[col].isnull().sum() > 0:
            if strategy == "median":
                fill_val = df_clean[col].median()
                df_clean[col] = df_clean[col].fillna(fill_val)
            elif strategy == "mean":
                fill_val = df_clean[col].mean()
                df_clean[col] = df_clean[col].fillna(fill_val)
                
    return df_clean

def handle_outliers_iqr(df: pd.DataFrame, columns: list = None, factor: float = 1.5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    FR-006: Outliers handling using IQR Clipping (Winsorization).
    Đảm bảo GIỮ NGUYÊN số lượng dòng (row count).
    """
    df_clipped = df.copy()
    if columns is None:
        columns = ['Recency', 'Frequency', 'Monetary']
        
    iqr_bounds = {}
    
    for col in columns:
        if col in df_clipped.columns:
            Q1 = df_clipped[col].quantile(0.25)
            Q3 = df_clipped[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - factor * IQR
            upper_bound = Q3 + factor * IQR
            
            iqr_bounds[col] = {
                "Q1": Q1,
                "Q3": Q3,
                "IQR": IQR,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            }
            
            # Clipping/Winsorization: Giới hạn giá trị trong khoảng [lower_bound, upper_bound]
            df_clipped[col] = np.clip(df_clipped[col], lower_bound, upper_bound)
            
    return df_clipped, iqr_bounds

def scale_rfm_features(df: pd.DataFrame, feature_cols: list = None) -> Tuple[np.ndarray, StandardScaler, pd.DataFrame]:
    """
    FR-007: Feature Scaling bằng StandardScaler.
    Lưu ý:
    - Chỉ áp dụng scaler trên 3 đặc trưng ['Recency', 'Frequency', 'Monetary'].
    - CustomerID tuyệt đối KHÔNG đưa vào scaler/model matrix.
    """
    if feature_cols is None:
        feature_cols = ['Recency', 'Frequency', 'Monetary']
        
    # Đảm bảo chỉ chọn đúng các cột RFM tồn tại
    valid_cols = [c for c in feature_cols if c in df.columns]
    
    scaler = StandardScaler()
    scaled_matrix = scaler.fit_transform(df[valid_cols])
    
    # Tạo DataFrame đã scale để phục vụ mục đích EDA/Trực quan hóa nếu cần
    df_scaled = df.copy()
    df_scaled[valid_cols] = scaled_matrix
    
    return scaled_matrix, scaler, df_scaled

def run_pipeline_preprocessing(df_raw: pd.DataFrame, missing_strategy: str = "median", outlier_strategy: str = "iqr_clip") -> Dict[str, Any]:
    """
    Pipeline chính kết hợp đầy đủ các bước tiền xử lý cho TV2 và trả về metadata cho TV3.
    """
    # 1. Quality check
    quality_report = check_data_quality(df_raw)
    
    # 2. Missing handling
    df_no_missing = handle_missing_values(df_raw, strategy=missing_strategy)
    
    # 3. Outlier handling (giữ nguyên row count)
    if outlier_strategy == "iqr_clip":
        df_clean, iqr_bounds = handle_outliers_iqr(df_no_missing)
    else:
        df_clean = df_no_missing.copy()
        iqr_bounds = {}
        
    # 4. Scaling (loại bỏ CustomerID khỏi ma trận đầu ra)
    scaled_matrix, scaler, df_scaled = scale_rfm_features(df_clean)
    
    return {
        "quality_report": quality_report,
        "processed_df": df_clean,
        "scaled_df": df_scaled,
        "scaled_matrix": scaled_matrix,  # Ma trận truyền trực tiếp cho TV3 K-Means
        "scaler": scaler,
        "iqr_bounds": iqr_bounds
    }

