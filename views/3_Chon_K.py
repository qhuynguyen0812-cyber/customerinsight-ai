"""TV3 candidate-K analysis and explicit K confirmation page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from components.states import get_app_state
from components.workflow import consume_flash, set_flash
from src.clustering import (
    analyze_candidate_k,
    get_default_solver_kwargs,
    recommend_k,
)
from src.state import set_k_analysis, set_selected_k

st.set_page_config(page_title="Phân tích và Chọn K", layout="wide")
st.title("Phân tích và Chọn K")

state = get_app_state()
flash = consume_flash(st.session_state)
if flash is not None:
    getattr(st, flash.level, st.info)(flash.text)

if state.scaled_matrix is None:
    st.info("Hãy hoàn thành bước tiền xử lý dữ liệu trước khi phân tích K.")
    st.stop()

n_samples = len(state.scaled_matrix)
if n_samples < 3:
    st.error("Cần ít nhất 3 khách hàng để phân tích Silhouette.")
    st.stop()

solver = get_default_solver_kwargs()
if isinstance(state.solver_preferences, dict):
    solver.update(state.solver_preferences)
st.caption(
    "Cấu hình: init={init}, n_init={n_init}, random_state={random_state}, "
    "max_iter={max_iter}, tol={tol}".format(**solver)
)

st.subheader("1. Phân tích Candidate K")
upper_limit = min(20, n_samples - 1)
default_max = min(10, upper_limit)
col1, col2 = st.columns(2)
with col1:
    k_min = int(st.number_input("K nhỏ nhất", min_value=2, max_value=upper_limit, value=2))
with col2:
    k_max = int(
        st.number_input(
            "K lớn nhất",
            min_value=2,
            max_value=upper_limit,
            value=max(2, default_max),
        )
    )

if st.button("Phân tích K", type="primary"):
    try:
        # Compute all artifacts locally; canonical state is untouched on failure.
        metrics = analyze_candidate_k(
            state.scaled_matrix,
            k_min,
            k_max,
            solver_kwargs=state.solver_preferences,
        )
        recommendation = recommend_k(metrics)
        set_k_analysis(state, metrics, recommendation)
    except (TypeError, ValueError) as exc:
        st.error(f"Không thể phân tích K: {exc}")
    else:
        set_flash(st.session_state, "Đã hoàn thành phân tích K.")
        st.rerun()

if state.k_metrics is None:
    st.info("Chọn khoảng K và nhấn **Phân tích K** để tính Elbow và Silhouette.")
    st.stop()

metrics_df = pd.DataFrame(state.k_metrics)
left, right = st.columns(2)
with left:
    st.plotly_chart(
        px.line(metrics_df, x="k", y="inertia", title="Elbow (Inertia)", markers=True),
        use_container_width=True,
    )
with right:
    st.plotly_chart(
        px.line(
            metrics_df,
            x="k",
            y="silhouette",
            title="Silhouette Score",
            markers=True,
        ),
        use_container_width=True,
    )
st.dataframe(metrics_df, use_container_width=True, hide_index=True)
st.info(f"K được đề xuất theo Silhouette: **{state.recommended_k}**")

st.subheader("2. Xác nhận K")
candidates = [int(k) for k in state.k_metrics["k"]]
default_k = state.selected_k if state.selected_k in candidates else state.recommended_k
selected_k = st.selectbox(
    "Chọn số cụm (K)",
    candidates,
    index=candidates.index(default_k),
)
if st.button("Xác nhận K"):
    set_selected_k(state, int(selected_k))
    set_flash(st.session_state, f"Đã xác nhận K = {selected_k}.")
    st.rerun()

if state.selected_k is not None:
    st.success(f"K đã xác nhận: {state.selected_k}")
