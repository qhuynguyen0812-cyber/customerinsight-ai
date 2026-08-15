"""Trang Dữ liệu: load/upload, validate, then atomically commit raw state."""

from pathlib import Path

import pandas as pd
import streamlit as st

from components.states import get_app_state
from components.workflow import consume_flash, set_flash
from src.state import set_raw_dataset
from src.validation import (
    DataValidationError,
    build_quality_report,
    load_csv_bytes,
    load_sample_dataset,
)


SAMPLE_PATH = Path(__file__).parents[1] / "data" / "sample_customers.csv"


def commit_validated(result) -> None:
    """Commit only a fully validated result and invalidate stale descendants."""

    state = get_app_state()
    set_raw_dataset(state, result.raw_df, result.dataset_signature)
    set_flash(st.session_state, f"Đã nạp thành công {len(result.raw_df)} khách hàng.")
    st.rerun()


def render_quality(raw_df: pd.DataFrame) -> None:
    report = build_quality_report(raw_df)
    st.subheader("Chất lượng dữ liệu")
    col1, col2, col3 = st.columns(3)
    col1.metric("Số khách hàng", report.row_count)
    col2.metric("Giá trị thiếu RFM", sum(report.missing_by_column.values()))
    col3.metric("IQR outlier", sum(report.iqr_outlier_by_column.values()))
    quality_df = pd.DataFrame(
        {
            "Missing": {name: report.missing_by_column[name] for name in ("Recency", "Frequency", "Monetary")},
            "IQR outlier": report.iqr_outlier_by_column,
        }
    )
    st.dataframe(quality_df, use_container_width=True)
    if report.zero_variance_columns:
        st.warning("Cột không có độ biến thiên: " + ", ".join(report.zero_variance_columns))


st.title("Dữ liệu khách hàng")
st.caption("Nạp dataset mẫu hoặc tải CSV có CustomerID, Recency, Frequency và Monetary.")

flash = consume_flash(st.session_state)
if flash is not None:
    getattr(st, flash.level, st.info)(flash.text)

sample_col, upload_col = st.columns(2)
with sample_col:
    st.subheader("Dataset mẫu")
    st.write("Sử dụng bộ dữ liệu 720 khách hàng của nhóm.")
    if st.button("Dùng dataset mẫu", type="primary", use_container_width=True):
        try:
            result = load_sample_dataset(SAMPLE_PATH)
        except DataValidationError as exc:
            st.error(str(exc))
        else:
            commit_validated(result)

with upload_col:
    st.subheader("Tải lên CSV")
    uploaded = st.file_uploader("Chọn file CSV", type=["csv"])
    if st.button("Kiểm tra và sử dụng CSV", disabled=uploaded is None, use_container_width=True):
        try:
            result = load_csv_bytes(uploaded.getvalue())
        except DataValidationError as exc:
            st.error(str(exc))
        else:
            commit_validated(result)

state = get_app_state()
if state.raw_df is None:
    st.info("Chưa có dataset hợp lệ. Hãy dùng dataset mẫu hoặc tải lên một file CSV.")
else:
    st.success("Dataset hiện tại đã hợp lệ.")
    st.code(f"SHA-256: {state.dataset_signature}", language=None)
    render_quality(state.raw_df)
    st.subheader("Xem trước dữ liệu")
    st.dataframe(state.raw_df.head(20), use_container_width=True)
