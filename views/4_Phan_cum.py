"""TV4 explicit clustering and profiling page."""

import streamlit as st

from components.states import get_app_state
from components.workflow import consume_flash, set_flash
from src.clustering import get_default_solver_kwargs
from src.profiling import run_clustering_workflow

st.set_page_config(page_title="Phân cụm", layout="wide")
st.title("Phân cụm khách hàng")

state = get_app_state()
flash = consume_flash(st.session_state)
if flash is not None:
    getattr(st, flash.level, st.info)(flash.text)

if state.scaled_matrix is None:
    st.info("Hãy hoàn thành bước tiền xử lý dữ liệu trước khi phân cụm.")
    st.stop()
if state.selected_k is None:
    st.info("Hãy phân tích và xác nhận K trước khi chạy K-Means.")
    st.stop()

solver = get_default_solver_kwargs()
if isinstance(state.solver_preferences, dict):
    solver.update(state.solver_preferences)
st.caption(
    "K={k}; init={init}; n_init={n_init}; random_state={random_state}; "
    "max_iter={max_iter}; tol={tol}".format(k=state.selected_k, **solver)
)

if st.button("Chạy K-Means", type="primary"):
    try:
        run_clustering_workflow(state)
    except (TypeError, ValueError) as exc:
        st.error(f"Không thể hoàn thành phân cụm: {exc}")
    else:
        set_flash(st.session_state, "Đã hoàn thành phân cụm và lập hồ sơ khách hàng.")
        st.rerun()

if state.cluster_profiles is not None:
    st.success("Kết quả phân cụm hiện tại đã sẵn sàng.")
    st.dataframe(state.cluster_profiles, use_container_width=True, hide_index=True)
    if state.run_metadata is not None:
        st.json(state.run_metadata)
