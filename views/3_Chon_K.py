"""Trang Phân tích và Chọn số cụm K tối ưu."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.states import get_app_state
from components.theme import apply_custom_theme
from components.workflow import consume_flash, set_flash
from src.clustering import (
    analyze_candidate_k,
    get_default_solver_kwargs,
    recommend_k,
)
from src.state import set_k_analysis, set_selected_k


def render_page() -> None:
    """Main render function for Step 3: Candidate-K Analysis & Confirmation."""
    apply_custom_theme()
    state = get_app_state()

    # --- HEADER ---
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <span class="ci-badge">BƯỚC 03 · CHỌN K</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("Tìm số cụm phù hợp")
    st.markdown(
        """
        <p style="font-size: 1.02rem; color: #464555; margin-bottom: 24px; max-width: 800px;">
            Đánh giá nhiều giá trị K bằng Elbow và Silhouette để lựa chọn cấu trúc phân cụm phù hợp.
        </p>
        """,
        unsafe_allow_html=True,
    )

    flash = consume_flash(st.session_state)
    if flash is not None:
        getattr(st, flash.level, st.info)(flash.text)

    # --- GATING / EMPTY STATE ---
    if state.scaled_matrix is None:
        st.info("Hãy hoàn thành bước tiền xử lý dữ liệu trước khi phân tích K.")
        st.stop()

    n_samples = len(state.scaled_matrix)
    if n_samples < 3:
        st.error("Cần ít nhất 3 khách hàng để phân tích Silhouette.")
        st.stop()

    # --- SOLVER CONFIG & CANDIDATE RANGE ---
    solver = get_default_solver_kwargs()
    if isinstance(state.solver_preferences, dict):
        solver.update(state.solver_preferences)

    st.markdown(
        f"""
        <div class="ci-banner" style="margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 36px; height: 36px; border-radius: 50%; background: rgba(53, 37, 205, 0.1); color: #3525cd; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                    ⚙
                </div>
                <div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #0b1c30;">Cấu hình K-Means Solver</div>
                    <div style="font-size: 0.82rem; color: #464555;">
                        init=<strong>{solver['init']}</strong> · n_init=<strong>{solver['n_init']}</strong> · random_state=<strong>{solver['random_state']}</strong> · max_iter=<strong>{solver['max_iter']}</strong> · tol=<strong>{solver['tol']}</strong>
                    </div>
                </div>
            </div>
            <div class="ci-stat-box" style="padding: 6px 14px;">
                <div style="font-size: 1.05rem; font-weight: 700; color: #0b1c30;">{n_samples:,}</div>
                <div style="font-size: 9px; font-weight: 600; color: #464555; text-transform: uppercase;">Mẫu chuẩn hóa</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    upper_limit = min(20, n_samples - 1)
    default_max = min(10, upper_limit)

    st.markdown(
        """
        <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;">
            Phạm vi đánh giá số cụm K
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_k1, col_k2, col_k_btn = st.columns([1, 1, 1.2], gap="medium")
    with col_k1:
        k_min = int(st.number_input("K nhỏ nhất", min_value=2, max_value=upper_limit, value=2))
    with col_k2:
        k_max = int(
            st.number_input(
                "K lớn nhất",
                min_value=2,
                max_value=upper_limit,
                value=max(2, default_max),
            )
        )
    with col_k_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_analyze = st.button("Phân tích K", type="primary", use_container_width=True)

    if btn_analyze:
        try:
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

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # --- ANALYTICAL WORKSPACE (ELBOW, SILHOUETTE, RECOMMENDATION) ---
    metrics_df = pd.DataFrame(state.k_metrics)
    k_list = [int(k) for k in metrics_df["k"]]
    rec_k = state.recommended_k

    # Find silhouette of recommended K
    rec_row = metrics_df[metrics_df["k"] == rec_k]
    rec_silhouette = float(rec_row["silhouette"].iloc[0]) if not rec_row.empty else 0.0

    col_elbow, col_sil, col_rec = st.columns([1.2, 1.2, 1.1], gap="medium")

    with col_elbow:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 0.95rem; font-weight: 700; color: #0b1c30; margin-bottom: 2px;">Elbow · Inertia</div>
                <div style="font-size: 0.78rem; color: #464555; margin-bottom: 10px;">Inertia giảm dần khi K tăng. Quan sát điểm gãy (elbow).</div>
            """,
            unsafe_allow_html=True,
        )
        fig_elbow = px.line(
            metrics_df,
            x="k",
            y="inertia",
            markers=True,
            color_discrete_sequence=["#3525cd"],
        )
        fig_elbow.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            plot_bgcolor="rgba(248, 249, 255, 0.6)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", size=11),
            xaxis=dict(tickmode="linear", dtick=1, title="Số cụm (K)"),
            yaxis=dict(title="Inertia"),
        )
        st.plotly_chart(fig_elbow, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_sil:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 0.95rem; font-weight: 700; color: #0b1c30; margin-bottom: 2px;">Silhouette Score</div>
                <div style="font-size: 0.78rem; color: #464555; margin-bottom: 10px;">Đo lường mức độ tách biệt cụm. Càng cao càng tốt.</div>
            """,
            unsafe_allow_html=True,
        )
        fig_sil = px.line(
            metrics_df,
            x="k",
            y="silhouette",
            markers=True,
            color_discrete_sequence=["#006a61"],
        )
        fig_sil.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            plot_bgcolor="rgba(248, 249, 255, 0.6)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", size=11),
            xaxis=dict(tickmode="linear", dtick=1, title="Số cụm (K)"),
            yaxis=dict(title="Silhouette Score"),
        )
        st.plotly_chart(fig_sil, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_rec:
        st.markdown(
            f"""
            <div class="ci-card" style="height: 100%; border: 1.5px solid rgba(53, 37, 205, 0.3); background: linear-gradient(180deg, #ffffff 0%, #eff4ff 100%); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 12px;">
                        <span style="color: #3525cd; font-size: 14px;">✦</span>
                        <div style="font-size: 11px; font-weight: 700; color: #3525cd; text-transform: uppercase; letter-spacing: 0.06em;">
                            Đề xuất từ phân tích
                        </div>
                    </div>
                    <div style="text-align: center; padding: 14px; background: #ffffff; border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 12px;">
                        <div style="font-size: 10px; font-weight: 600; color: #464555; text-transform: uppercase;">Silhouette cao nhất</div>
                        <div style="font-size: 2.2rem; font-weight: 800; color: #3525cd; line-height: 1.2;">K = {rec_k}</div>
                        <div style="font-size: 0.85rem; color: #006a61; font-weight: 700; margin-top: 4px;">Score: {rec_silhouette:.4f}</div>
                    </div>
                    <p style="font-size: 0.8rem; color: #464555; line-height: 1.5; margin: 0;">
                        K = {rec_k} đạt Silhouette Score cao nhất trong khoảng K đã khảo sát. Elbow đóng vai trò kiểm chứng sự suy giảm quán tính.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- CANDIDATE COMPARISON TABLE & EXPLANATION ---
    col_tbl, col_exp = st.columns([1.6, 1.1], gap="large")

    with col_tbl:
        st.markdown(
            """
            <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
                Bảng so sánh chi tiết các giá trị K
            </div>
            """,
            unsafe_allow_html=True,
        )
        display_df = metrics_df.copy()
        display_df["Đánh giá"] = display_df["k"].apply(
            lambda k: "★ Đề xuất (Silhouette cao nhất)" if k == rec_k else "—"
        )
        display_df["Inertia"] = display_df["inertia"].apply(lambda v: f"{v:.4f}")
        display_df["Silhouette Score"] = display_df["silhouette"].apply(lambda v: f"{v:.4f}")
        st.dataframe(
            display_df[["k", "Inertia", "Silhouette Score", "Đánh giá"]],
            width="stretch",
            hide_index=True,
        )

    with col_exp:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
                    Hướng dẫn đọc kết quả
                </div>
                <div style="margin-bottom: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #3525cd; margin-bottom: 2px;">Elbow (Inertia)</div>
                    <p style="font-size: 0.82rem; color: #464555; line-height: 1.5; margin: 0;">
                        Inertia đo tổng bình phương khoảng cách từ mỗi điểm đến tâm cụm. Điểm uốn (elbow) là nơi tốc độ giảm bắt đầu chững lại.
                    </p>
                </div>
                <div>
                    <div style="font-size: 0.88rem; font-weight: 700; color: #006a61; margin-bottom: 2px;">Silhouette Score</div>
                    <p style="font-size: 0.82rem; color: #464555; line-height: 1.5; margin: 0;">
                        Đo lường mức độ tương đồng của điểm với cụm của nó so với cụm khác (-1 đến 1). Giá trị đỉnh cao nhất là cơ sở chính để hệ thống đề xuất K.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

    # --- EXPLICIT K CONFIRMATION ---
    st.markdown(
        """
        <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            Xác nhận số cụm K cho mô hình phân cụm
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_k = state.selected_k if state.selected_k in k_list else state.recommended_k
    col_sel, col_confirm = st.columns([1.2, 1.2], gap="medium")
    with col_sel:
        selected_k = st.selectbox(
            "Chọn số cụm (K)",
            k_list,
            index=k_list.index(default_k) if default_k in k_list else 0,
            help="Bạn có thể chọn theo đề xuất của hệ thống hoặc tự điều chỉnh K theo nhu cầu phân đoạn kinh doanh.",
        )
    with col_confirm:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Xác nhận K", type="primary", use_container_width=True):
            set_selected_k(state, int(selected_k))
            set_flash(st.session_state, f"Đã xác nhận K = {selected_k}.")
            st.rerun()

    # --- CONFIRMED STATE & NEXT STEP CTA ---
    if state.selected_k is not None:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="ci-banner">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="width: 42px; height: 42px; border-radius: 50%; background: rgba(0, 106, 97, 0.12); color: #006a61; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: bold;">
                        ✓
                    </div>
                    <div>
                        <div style="font-size: 1.05rem; font-weight: 700; color: #0b1c30;">Đã xác nhận K = {state.selected_k}</div>
                        <div style="font-size: 0.85rem; color: #464555;">Mô hình K-Means đã sẵn sàng thực hiện huấn luyện phân cụm với {state.selected_k} phân khúc khách hàng.</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        col_c_pad, col_c_btn = st.columns([1, 1])
        with col_c_btn:
            if st.button("Tiếp tục: Phân cụm →", type="primary", use_container_width=True):
                st.switch_page("views/4_Phan_cum.py")
            st.caption("Bước tiếp theo: Huấn luyện K-Means và trực quan hóa các cụm khách hàng")


render_page()
