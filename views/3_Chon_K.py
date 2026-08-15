import streamlit as st
import pandas as pd
import plotly.express as px
from src.clustering import analyze_candidate_k, recommend_k

st.title("Phân tích và Chọn K")

# Kiểm tra State - Workflow gating (TV5 contract)
if 'df_scaled' not in st.session_state:
    st.warning("Vui lòng hoàn thành bước Tiền xử lý dữ liệu trước.")
    st.stop()

df_scaled = st.session_state['df_scaled']

st.subheader("1. Phân tích Candidate K (Elbow & Silhouette)")
col1, col2 = st.columns(2)
with col1:
    k_min = st.number_input("K nhỏ nhất", min_value=2, max_value=15, value=2)
with col2:
    k_max = st.number_input("K lớn nhất", min_value=3, max_value=20, value=10)

if k_min >= k_max:
    st.error("K lớn nhất phải lớn hơn K nhỏ nhất.")
else:
    with st.spinner("Đang tính toán các độ đo..."):
        analysis_results = analyze_candidate_k(df_scaled, k_min, k_max)
        df_metrics = pd.DataFrame(analysis_results)
        
        # Render Elbow Chart
        fig_elbow = px.line(df_metrics, x='k', y='inertia', title='Elbow Method (Inertia)', markers=True)
        st.plotly_chart(fig_elbow, use_container_width=True)
        
        # Render Silhouette Chart
        fig_sil = px.line(df_metrics, x='k', y='silhouette', title='Silhouette Score', markers=True)
        st.plotly_chart(fig_sil, use_container_width=True)
        
        rec_k = recommend_k(analysis_results)
        st.info(f"Dựa trên phân tích, K đề xuất là: **{rec_k}**")

st.subheader("2. Xác nhận K")
selected_k = st.number_input("Chọn số cụm (K) để tiến hành chạy mô hình:", min_value=2, max_value=20, value=int(rec_k) if 'rec_k' in locals() else 3)

if st.button("Xác nhận K và chuyển sang bước Phân cụm"):
    st.session_state['selected_k'] = selected_k
    st.success("Đã lưu cấu hình K. Chuyển state thành công!")