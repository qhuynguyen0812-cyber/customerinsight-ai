"""Trang Khám phá dữ liệu (EDA) & Tiền xử lý RFM."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.states import get_app_state
from components.theme import apply_custom_theme
from components.workflow import consume_flash, set_flash
from src.preprocessing import PreprocessingError, RFM_FEATURES, run_pipeline_preprocessing
from src.state import set_preprocessed_data


def render_pipeline_strip(is_processed: bool, raw_count: int) -> None:
    """Render the 5-step canonical preprocessing pipeline representation."""
    status_class = "✓ Hoàn tất" if is_processed else "Đang chờ"
    badge_bg = "#006a61" if is_processed else "#3525cd"

    st.markdown(
        f"""
        <div class="ci-pipeline-card" style="margin-bottom: 24px;">
            <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 16px;">
                Quy trình chuẩn hóa dữ liệu RFM
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px;">
                <div class="ci-step-card" style="padding: 14px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: {badge_bg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; margin-bottom: 8px;">1</div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #0b1c30;">Dữ liệu gốc</div>
                    <div style="font-size: 0.75rem; color: #464555; margin-top: 2px;">{raw_count:,} khách hàng, 3 RFM</div>
                    <div style="font-size: 0.72rem; color: #006a61; font-weight: 600; margin-top: 4px;">{status_class}</div>
                </div>
                <div class="ci-step-card" style="padding: 14px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: {badge_bg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; margin-bottom: 8px;">2</div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #0b1c30;">Giá trị thiếu</div>
                    <div style="font-size: 0.75rem; color: #464555; margin-top: 2px;">Median Imputation</div>
                    <div style="font-size: 0.72rem; color: #006a61; font-weight: 600; margin-top: 4px;">{status_class}</div>
                </div>
                <div class="ci-step-card" style="padding: 14px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: {badge_bg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; margin-bottom: 8px;">3</div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #0b1c30;">Ngoại lệ</div>
                    <div style="font-size: 0.75rem; color: #464555; margin-top: 2px;">IQR Clipping (1.5×IQR)</div>
                    <div style="font-size: 0.72rem; color: #006a61; font-weight: 600; margin-top: 4px;">{status_class}</div>
                </div>
                <div class="ci-step-card" style="padding: 14px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: {badge_bg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; margin-bottom: 8px;">4</div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #0b1c30;">Chuẩn hóa</div>
                    <div style="font-size: 0.75rem; color: #464555; margin-top: 2px;">StandardScaler (R, F, M)</div>
                    <div style="font-size: 0.72rem; color: #006a61; font-weight: 600; margin-top: 4px;">{status_class}</div>
                </div>
                <div class="ci-step-card" style="padding: 14px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: {badge_bg}; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; margin-bottom: 8px;">5</div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #0b1c30;">Model Ready</div>
                    <div style="font-size: 0.75rem; color: #464555; margin-top: 2px;">Sẵn sàng cho K-Means</div>
                    <div style="font-size: 0.72rem; color: #006a61; font-weight: 600; margin-top: 4px;">{status_class}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page() -> None:
    """Main render function for Step 2: Exploratory Data Analysis & Preprocessing."""
    apply_custom_theme()
    state = get_app_state()

    # --- HEADER ---
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <span class="ci-badge">BƯỚC 02 · KHÁM PHÁ DỮ LIỆU</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("Hiểu dữ liệu trước khi phân cụm")
    st.markdown(
        """
        <p style="font-size: 1.02rem; color: #464555; margin-bottom: 24px; max-width: 800px;">
            Làm sạch, xử lý ngoại lệ và chuẩn hóa các đặc trưng RFM trước khi phân tích cấu trúc cụm.
        </p>
        """,
        unsafe_allow_html=True,
    )

    flash = consume_flash(st.session_state)
    if flash is not None:
        getattr(st, flash.level, st.info)(flash.text)

    # --- GATING / EMPTY STATE ---
    if state.raw_df is None or state.dataset_signature is None:
        st.info(
            "Chưa có bộ dữ liệu hợp lệ. Hãy mở trang **Dữ liệu**, tải hoặc chọn "
            "dữ liệu mẫu, rồi quay lại đây."
        )
        st.stop()

    is_processed = state.processed_df is not None and state.scaled_matrix is not None
    render_pipeline_strip(is_processed, len(state.raw_df))

    # --- PREPROCESSING ACTION ---
    if not is_processed:
        st.markdown(
            """
            <div class="ci-card" style="margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                    <div>
                        <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin-bottom: 4px;">
                            Bắt đầu tiền xử lý dữ liệu
                        </h3>
                        <p style="font-size: 0.9rem; color: #464555; margin: 0;">
                            Hệ thống sẽ thực hiện Median Imputation cho giá trị thiếu, IQR Clipping giới hạn ngoại lệ và StandardScaler cho các đặc trưng RFM.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Xử lý dữ liệu", type="primary", use_container_width=True):
            try:
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

        st.stop()

    # --- SUCCESS PANEL & DETAILS ---
    df = state.processed_df
    col_summary, col_tech = st.columns([1.6, 1.4], gap="large")

    with col_summary:
        st.markdown(
            f"""
            <div class="ci-card" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                        <span style="color: #006a61; font-weight: bold; font-size: 20px;">✓</span>
                        <h3 style="font-size: 1.1rem; font-weight: 700; color: #0b1c30; margin: 0;">
                            Dữ liệu đã sẵn sàng cho phân tích K
                        </h3>
                    </div>
                    <p style="font-size: 0.88rem; color: #464555; margin-bottom: 16px;">
                        Ba đặc trưng Recency, Frequency, Monetary đã được làm sạch và chuẩn hóa.
                    </p>
                </div>
                <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                    <div class="ci-stat-box">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #0b1c30;">{len(df):,}</div>
                        <div style="font-size: 10px; font-weight: 600; color: #464555; text-transform: uppercase;">Khách hàng</div>
                    </div>
                    <div class="ci-stat-box">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #0b1c30;">3</div>
                        <div style="font-size: 10px; font-weight: 600; color: #464555; text-transform: uppercase;">Đặc trưng RFM</div>
                    </div>
                    <div class="ci-stat-box">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #0b1c30;">0</div>
                        <div style="font-size: 10px; font-weight: 600; color: #464555; text-transform: uppercase;">Giá trị thiếu</div>
                    </div>
                    <div class="ci-stat-box" style="background: rgba(0, 106, 97, 0.08); border-color: rgba(0, 106, 97, 0.2);">
                        <div style="font-size: 0.95rem; font-weight: 700; color: #006a61; margin-top: 4px;">Model Ready</div>
                        <div style="font-size: 10px; font-weight: 600; color: #006a61; text-transform: uppercase;">Trạng thái</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_tech:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
                    Chi tiết kỹ thuật tiền xử lý
                </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Median Imputation", expanded=False):
            st.write(
                "Điền giá trị thiếu độc lập cho từng thuộc tính bằng giá trị trung vị (median) để giảm thiểu ảnh hưởng của các ngoại lệ cực đoan."
            )
        with st.expander("IQR Clipping (Winsorization)", expanded=False):
            st.write(
                "Giới hạn giá trị trong khoảng [Q1 - 1.5×IQR, Q3 + 1.5×IQR] nhằm hạn chế sự bóp méo trọng tâm cụm của thuật toán K-Means."
            )
        with st.expander("StandardScaler (Chuẩn hóa z-score)", expanded=False):
            st.write(
                "Chuẩn hóa về mean=0 và std=1 chỉ trên 3 đặc trưng RFM để đảm bảo khoảng cách Euclid công bằng. CustomerID giữ nguyên định danh."
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- BEFORE / AFTER RFM SUMMARY ---
    st.markdown(
        """
        <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 14px;">
            Trước và sau tiền xử lý (Giới hạn ngoại lệ)
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_r, c_f, c_m = st.columns(3, gap="medium")
    for col, feat in zip([c_r, c_f, c_m], RFM_FEATURES):
        raw_max = float(state.raw_df[feat].max())
        proc_max = float(df[feat].max())
        if raw_max > 0 and raw_max > proc_max:
            red_pct = (raw_max - proc_max) / raw_max * 100.0
            red_text = f"Giới hạn cực trị: {red_pct:.1f}%"
        else:
            red_text = "Không có ngoại lệ vượt ngưỡng"

        with col:
            st.markdown(
                f"""
                <div class="ci-before-after-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span style="font-size: 0.95rem; font-weight: 700; color: #0b1c30; text-transform: uppercase;">{feat}</span>
                        <span style="background: #e5eeff; color: #3525cd; font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px;">Đã xử lý IQR</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85rem;">
                        <div>
                            <div style="font-size: 10px; color: #464555; text-transform: uppercase; font-weight: 600;">Trước (Max)</div>
                            <div style="font-size: 1.1rem; color: #ba1a1a; text-decoration: line-through;">{raw_max:g}</div>
                        </div>
                        <div>
                            <div style="font-size: 10px; color: #464555; text-transform: uppercase; font-weight: 600;">Sau IQR (Max)</div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #006a61;">{proc_max:g}</div>
                            <div style="font-size: 10px; color: #464555; margin-top: 2px;">{red_text}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --- IQR BOUNDS DETAILS (EXPANDABLE) ---
    summary = state.eda_summary if isinstance(state.eda_summary, dict) else {}
    bounds = summary.get("iqr_bounds", {})
    if bounds:
        with st.expander("Xem chi tiết ngưỡng IQR đã áp dụng", expanded=False):
            bounds_rows = []
            for feature in RFM_FEATURES:
                if feature in bounds:
                    b = bounds[feature]
                    bounds_rows.append(
                        {
                            "Đặc trưng": feature,
                            "Q1 (25%)": f"{b.get('q1', 0):.2f}",
                            "Q3 (75%)": f"{b.get('q3', 0):.2f}",
                            "IQR": f"{b.get('iqr', 0):.2f}",
                            "Cận dưới": f"{b.get('lower_bound', 0):.2f}",
                            "Cận trên": f"{b.get('upper_bound', 0):.2f}",
                        }
                    )
            if bounds_rows:
                st.dataframe(pd.DataFrame(bounds_rows), width="stretch", hide_index=True)

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- DISTRIBUTION EXPLORATION ---
    st.markdown(
        """
        <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            Khám phá phân phối RFM
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_hist, tab_box = st.tabs(["Histogram", "Boxplot"])
    with tab_hist:
        selected = st.selectbox("Chọn đặc trưng", list(RFM_FEATURES))
        fig_hist = px.histogram(
            df,
            x=selected,
            nbins=30,
            marginal="rug",
            title=f"Phân phối {selected} (sau tiền xử lý)",
            color_discrete_sequence=["#3525cd"],
        )
        fig_hist.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="rgba(248, 249, 255, 0.6)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig_hist, width="stretch")

    with tab_box:
        fig_box = px.box(
            df,
            y=list(RFM_FEATURES),
            title="Phân bố đặc trưng RFM sau IQR clipping",
            color_discrete_sequence=["#3525cd", "#006a61", "#8b5cf6"],
        )
        fig_box.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="rgba(248, 249, 255, 0.6)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig_box, width="stretch")

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- CORRELATION SECTION ---
    st.markdown(
        """
        <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            Tương quan giữa các đặc trưng
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_corr_chart, col_corr_note = st.columns([1.6, 1.4], gap="large")
    correlation = df.loc[:, list(RFM_FEATURES)].corr().round(2)

    with col_corr_chart:
        fig_corr = px.imshow(
            correlation,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Tương quan Pearson giữa Recency, Frequency và Monetary",
        )
        fig_corr.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig_corr, width="stretch")

    with col_corr_note:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 11px; font-weight: 700; color: #3525cd; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
                    ✦ NHẬN XÉT TƯƠNG QUAN
                </div>
                <p style="font-size: 0.9rem; color: #464555; line-height: 1.6; margin-bottom: 12px;">
                    • <strong>Frequency & Monetary:</strong> Có xu hướng tương quan thuận rõ rệt (khách hàng mua thường xuyên thường chi tiêu nhiều hơn).
                </p>
                <p style="font-size: 0.9rem; color: #464555; line-height: 1.6; margin: 0;">
                    • <strong>Recency:</strong> Thường tương quan âm với Frequency và Monetary (khách hàng mới mua gần đây có xu hướng tích cực hơn nhóm lâu chưa quay lại).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- DESCRIPTIVE STATISTICS (POST-IQR) ---
    with st.expander("Thống kê mô tả chi tiết RFM (sau tiền xử lý)", expanded=False):
        st.dataframe(df.loc[:, list(RFM_FEATURES)].describe(), width="stretch")

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- BOTTOM NEXT STEP ACTION ---
    st.markdown(
        """
        <div class="ci-banner">
            <div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #0b1c30; margin-bottom: 2px;">
                    Dữ liệu đã sẵn sàng cho bước tiếp theo
                </div>
                <div style="font-size: 0.85rem; color: #464555;">
                    Ba đặc trưng RFM đã được làm sạch và chuẩn hóa để phân tích số cụm tối ưu.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_pad, col_btn = st.columns([1, 1])
    with col_btn:
        if st.button("Tiếp tục: Chọn K →", type="primary", use_container_width=True):
            st.switch_page("views/3_Chon_K.py")
        st.caption("Bước tiếp theo: Đánh giá số cụm tối ưu bằng Elbow và Silhouette Score")


render_page()
