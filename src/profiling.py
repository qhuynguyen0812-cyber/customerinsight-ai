"""
Module tính toán Cluster Profiling và Business Interpretation cho RFM.
"""
from typing import Dict
import pandas as pd

FEATURE_COLS = ["Recency", "Frequency", "Monetary"]


def compute_cluster_profiles(
    original_df: pd.DataFrame, 
    cluster_labels: pd.Series
) -> pd.DataFrame:
    """
    Tính toán bảng thống kê chi tiết của từng cụm trên dữ liệu gốc.
    """
    if original_df.empty or len(original_df) != len(cluster_labels):
        raise ValueError("Dữ liệu gốc và nhãn cụm không khớp kích thước hoặc bị rỗng.")

    df = original_df.copy()
    df["Cluster"] = cluster_labels

    summary_list = []
    total_customers = len(df)

    for cluster_id, group in df.groupby("Cluster"):
        row = {
            "Cluster": int(cluster_id),
            "Count": len(group),
            "Percentage": round((len(group) / total_customers) * 100, 2),
            "Recency_Mean": round(group["Recency"].mean(), 2),
            "Recency_Median": round(group["Recency"].median(), 2),
            "Recency_Min": round(group["Recency"].min(), 2),
            "Recency_Max": round(group["Recency"].max(), 2),
            "Recency_Std": round(group["Recency"].std(), 2) if len(group) > 1 else 0.0,
            "Frequency_Mean": round(group["Frequency"].mean(), 2),
            "Frequency_Median": round(group["Frequency"].median(), 2),
            "Frequency_Min": round(group["Frequency"].min(), 2),
            "Frequency_Max": round(group["Frequency"].max(), 2),
            "Frequency_Std": round(group["Frequency"].std(), 2) if len(group) > 1 else 0.0,
            "Monetary_Mean": round(group["Monetary"].mean(), 2),
            "Monetary_Median": round(group["Monetary"].median(), 2),
            "Monetary_Min": round(group["Monetary"].min(), 2),
            "Monetary_Max": round(group["Monetary"].max(), 2),
            "Monetary_Std": round(group["Monetary"].std(), 2) if len(group) > 1 else 0.0,
        }
        summary_list.append(row)

    profile_df = pd.DataFrame(summary_list)
    return profile_df


def generate_business_interpretation(profile_df: pd.DataFrame) -> Dict[int, Dict[str, str]]:
    """
    Tự động phân loại đặc điểm kinh doanh của từng cụm dựa trên 
    so sánh tương quan giá trị trung bình RFM giữa các cụm.
    """
    interpretations = {}

    avg_r = profile_df["Recency_Mean"].mean()
    avg_f = profile_df["Frequency_Mean"].mean()
    avg_m = profile_df["Monetary_Mean"].mean()

    for _, row in profile_df.iterrows():
        c_id = int(row["Cluster"])
        r_val = row["Recency_Mean"]
        f_val = row["Frequency_Mean"]
        m_val = row["Monetary_Mean"]

        r_tag = "Gần đây" if r_val <= avg_r else "Đã lâu"
        f_tag = "Tần suất cao" if f_val >= avg_f else "Tần suất thấp"
        m_tag = "Chi tiêu cao" if m_val >= avg_m else "Chi tiêu thấp"

        if r_val <= avg_r and f_val >= avg_f and m_val >= avg_m:
            segment_name = "Khách hàng VIP / Trung thành"
            action = "Chăm sóc đặc biệt, chương trình tri ân và duy trì quyền lợi cao cấp."
        elif r_val > avg_r and f_val < avg_f and m_val < avg_m:
            segment_name = "Khách hàng Ngủ đông / Rời bỏ"
            action = "Gửi chiến dịch tái kích hoạt, khảo sát lý do ngừng mua."
        elif r_val <= avg_r and (f_val < avg_f or m_val < avg_m):
            segment_name = "Khách hàng Mới / Tiềm năng"
            action = "Khuyến khích gia tăng đơn hàng tiếp theo thông qua ưu đãi."
        else:
            segment_name = "Khách hàng Trung bình / Cần kích cầu"
            action = "Cung cấp ưu đãi cá nhân hóa để tăng tần suất và giá trị đơn hàng."

        interpretations[c_id] = {
            "segment_name": segment_name,
            "characteristics": f"{r_tag}, {f_tag}, {m_tag}",
            "recommendation": action
        }

    return interpretations