"""TV2 preprocessing action and read-only EDA page."""

import plotly.express as px
import streamlit as st

from components.states import get_app_state
from components.workflow import consume_flash, set_flash
from src.preprocessing import PreprocessingError, RFM_FEATURES, run_pipeline_preprocessing
from src.state import set_preprocessed_data

st.set_page_config(page_title="Khám phá dữ liệu (EDA)", layout="wide")
st.title("📊 Khám phá dữ liệu (EDA & Data Quality)")
st.write("Tiền xử lý dữ liệu cục bộ và khám phá phân phối RFM.")

state = get_app_state()
flash = consume_flash(st.session_state)
if flash is not None:
    getattr(st, flash.level, st.info)(flash.text)

if state.raw_df is None or state.dataset_signature is None:
    st.info(
        "Chưa có bộ dữ liệu hợp lệ. Hãy mở trang **Dữ liệu**, tải hoặc chọn "
        "dữ liệu mẫu, rồi quay lại đây."
    )
    st.stop()

st.caption(f"Dữ liệu đầu vào: {len(state.raw_df):,} khách hàng")
if st.button("Xử lý dữ liệu", type="primary"):
    try:
        # Build every artifact locally. Canonical state remains untouched if this fails.
        result = run_pipeline_preprocessing(state.raw_df)
        set_preprocessed_data(
            state,
            processed_df=result["processed_df"],
            scaled_matrix=result["scaled_matrix"],
            preprocessing_signature=result["preprocessing_signature"],
            eda_summary=result["eda_summary"],
        )
    except PreprocessingError as exc:
        st.error(f"Không thể xử lý dữ liệu: {exc}")
    else:
        set_flash(st.session_state, "Đã xử lý dữ liệu thành công.")
        st.rerun()

if state.processed_df is None:
    st.info("Dữ liệu chưa được tiền xử lý. Chọn **Xử lý dữ liệu** để tiếp tục.")
    st.stop()

df = state.processed_df
st.success("Dữ liệu RFM đã được tiền xử lý và sẵn sàng cho phân tích.")

st.header("1. Tổng quan và chất lượng dữ liệu")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Số bản ghi", len(df))
col2.metric("Số thuộc tính", len(df.columns))
col3.metric("Giá trị RFM còn thiếu", int(df.loc[:, list(RFM_FEATURES)].isna().sum().sum()))
col4.metric("Dòng trùng lặp", int(df.duplicated().sum()))

st.subheader("Dữ liệu sau tiền xử lý")
st.dataframe(df.head(10), use_container_width=True)
st.subheader("Thống kê mô tả RFM")
st.dataframe(df.loc[:, list(RFM_FEATURES)].describe(), use_container_width=True)

summary = state.eda_summary if isinstance(state.eda_summary, dict) else {}
bounds = summary.get("iqr_bounds", {})
if bounds:
    st.subheader("Ngưỡng IQR đã áp dụng")
    st.dataframe(
        {
            feature: {
                "Cận dưới": values["lower_bound"],
                "Cận trên": values["upper_bound"],
            }
            for feature, values in bounds.items()
        }
    )

st.header("2. Phân phối RFM")
tab_hist, tab_box = st.tabs(["Histogram", "Boxplot"])
with tab_hist:
    selected = st.selectbox("Chọn đặc trưng", list(RFM_FEATURES))
    st.plotly_chart(
        px.histogram(df, x=selected, nbins=30, marginal="rug", title=f"Phân phối {selected}"),
        use_container_width=True,
    )
with tab_box:
    st.plotly_chart(
        px.box(df, y=list(RFM_FEATURES), title="RFM sau IQR clipping"),
        use_container_width=True,
    )

st.header("3. Tương quan RFM")
correlation = df.loc[:, list(RFM_FEATURES)].corr().round(2)
st.plotly_chart(
    px.imshow(
        correlation,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
        title="Tương quan Pearson giữa Recency, Frequency và Monetary",
    ),
    use_container_width=True,
)
