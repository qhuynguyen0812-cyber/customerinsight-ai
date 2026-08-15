"""TV5-owned overview and canonical workflow entry point."""

import streamlit as st

from components.states import get_app_state
from components.workflow import workflow_stage


state = get_app_state()

st.title("CustomerInsight AI")
st.write("Phân khúc khách hàng bằng K-Means dựa trên RFM.")

st.subheader("Bắt đầu phân tích")
st.write(
    "Tải dữ liệu CSV, xử lý dữ liệu, phân tích K và chạy K-Means theo workflow "
    "của ứng dụng."
)

col1, col2 = st.columns(2)
with col1:
    st.info("**Dataset mẫu**\n\nSử dụng dataset mẫu để đi theo canonical flow.")
with col2:
    st.info(
        "**Tải lên CSV**\n\nDùng dữ liệu của bạn với schema CustomerID, Recency, "
        "Frequency, Monetary."
    )

st.caption("Workflow: Dữ liệu → Khám phá dữ liệu → Chọn K → Phân cụm → Kết quả")
st.caption(f"Current stage: {workflow_stage(state).name.replace('_', ' ').title()}")
