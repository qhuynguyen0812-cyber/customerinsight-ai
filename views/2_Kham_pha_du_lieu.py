import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff

st.set_page_config(page_title="Khám phá Dữ liệu (EDA)", layout="wide")

st.title("📊 Khám phá Dữ liệu (EDA & Data Quality)")
st.write("Báo cáo phân tích chất lượng dữ liệu và phân phối RFM (TV2 - Preprocessing & EDA)")

# Kiểm tra dữ liệu trong session_state
if "processed_df" in st.session_state and st.session_state["processed_df"] is not None:
    df = st.session_state["processed_df"]
    
    st.success("✅ Đã nhận dữ liệu đã qua tiền xử lý (Processed State).")
    
    # --- SECTION 1: Tổng quan & Data Quality ---
    st.header("1. Tổng quan & Chất lượng Dữ liệu")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng số bản ghi (Rows)", len(df))
    col2.metric("Số lượng thuộc tính", len(df.columns))
    col3.metric("Số bản ghi thiếu (Missing)", df.isnull().sum().sum())
    col4.metric("Số dòng trùng lặp", df.duplicated().sum())
    
    st.subheader("Xem trước dữ liệu")
    st.dataframe(df.head(10), use_container_width=True)
    
    # --- SECTION 2: Phân tích Phân phối RFM (Distribution & Outliers) ---
    st.header("2. Phân tích Phân phối Đặc trưng RFM")
    
    rfm_cols = [c for c in ['Recency', 'Frequency', 'Monetary'] if c in df.columns]
    
    if rfm_cols:
        tab1, tab2 = st.tabs(["📈 Biểu đồ Phân phối (Histogram)", "📦 Biểu đồ Hộp (Boxplot - Outliers)"])
        
        with tab1:
            selected_col = st.selectbox("Chọn thuộc tính RFM để xem phân phối:", rfm_cols)
            fig_hist = px.histogram(
                df, 
                x=selected_col, 
                nbins=30, 
                marginal="rug", 
                title=f"Phân phối của {selected_col}",
                color_discrete_sequence=['#2b5c8f']
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
        with tab2:
            fig_box = px.box(
                df, 
                y=rfm_cols, 
                title="Phân bố Outlier trên các đặc trưng RFM (Sau khi Clipping)",
                color_discrete_sequence=['#e74c3c']
            )
            st.plotly_chart(fig_box, use_container_width=True)
            
        # --- SECTION 3: Phân tích Tương quan (Correlation Matrix) ---
        st.header("3. Ma trận Tương quan")
        corr = df[rfm_cols].corr().round(2)
        fig_corr = px.imshow(
            corr, 
            text_auto=True, 
            aspect="auto", 
            color_continuous_scale="RdBu_r",
            title="Tương quan Pearson giữa Recency, Frequency, Monetary"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        
    else:
        st.warning("⚠️ Không tìm thấy các cột Recency, Frequency, Monetary trong dữ liệu.")

else:
    st.info("ℹ️ Chưa có dữ liệu được tải lên. Vui lòng quay lại trang **1. Dữ liệu** để nhập/tải dữ liệu đầu vào.")