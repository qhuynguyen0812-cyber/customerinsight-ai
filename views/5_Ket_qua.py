"""Trang Kết quả phân cụm (Customer Intelligence & Export)."""

from __future__ import annotations

from collections.abc import Mapping
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.results_export import (
    CUSTOMER_RESULT_COLUMNS,
    ResultContractError,
    available_run_metadata,
    customer_results_to_csv_bytes,
    validate_customer_results,
    validate_profile,
)
from components.states import APP_STATE_KEY, get_app_state
from components.theme import apply_custom_theme

# TV5 owns these state values. TV6 documents this consumer seam and never
# mutates them. The validity flag must only be true for the active signatures.
RESULTS_VALID_KEY = "results_valid"
CUSTOMER_RESULTS_KEY = "customer_results"
CLUSTER_PROFILES_KEY = "cluster_profiles"
RUN_METADATA_KEY = "run_metadata"

CLUSTER_PALETTE = [
    "#3525cd",  # Cluster 0 / 01: Primary Indigo
    "#006a61",  # Cluster 1 / 02: Secondary Teal
    "#8b5cf6",  # Cluster 2 / 03: Accent Violet
    "#2563eb",  # Cluster 3 / 04: Blue
    "#059669",  # Cluster 4 / 05: Emerald
    "#d97706",  # Cluster 5 / 06: Amber
    "#dc2626",  # Cluster 6 / 07: Red
]


def _page_state():
    """Prefer canonical AppState; use flat keys only as a compatibility adapter."""
    if APP_STATE_KEY in st.session_state:
        return get_app_state()
    return st.session_state


def render_results_page(state) -> None:
    """Render only outputs declared current by the upstream state owner."""
    apply_custom_theme()

    legacy = isinstance(state, Mapping)
    results_valid = state.get(RESULTS_VALID_KEY) is True if legacy else all(
        value is not None
        for value in (state.results, state.cluster_profiles, state.run_metadata)
    )

    # --- HEADER ---
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <span class="ci-badge">BƯỚC 05 · KẾT QUẢ</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("Customer Intelligence")
    st.markdown(
        """
        <p style="font-size: 1.02rem; color: #464555; margin-bottom: 24px; max-width: 800px;">
            Khám phá các phân khúc, tìm kiếm từng khách hàng và xuất kết quả phân tích.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # --- GATING / INVALID STATE ---
    if not results_valid:
        st.info("Chưa có kết quả hợp lệ. Hãy hoàn tất bước Phân cụm trước khi xem hoặc xuất dữ liệu.")
        return

    try:
        customers = validate_customer_results(
            state.get(CUSTOMER_RESULTS_KEY) if legacy else state.results
        )
    except ResultContractError as error:
        st.error(f"Không thể hiển thị kết quả hiện tại: {error}")
        return

    profile = state.get(CLUSTER_PROFILES_KEY) if legacy else state.cluster_profiles
    metadata = state.get(RUN_METADATA_KEY) if legacy else state.run_metadata
    try:
        current_profile = validate_profile(profile)
        current_metadata = available_run_metadata(metadata)
    except ResultContractError as error:
        st.error(f"Kết quả hiện tại chưa đầy đủ: {error}")
        return

    total_customers = len(customers)
    num_clusters = len(current_profile)

    # Status Banner
    st.markdown(
        f"""
        <div class="ci-banner" style="margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 38px; height: 38px; border-radius: 50%; background: rgba(0, 106, 97, 0.12); color: #006a61; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px;">
                    ✓
                </div>
                <div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0b1c30;">Phân tích hoàn tất</div>
                    <div style="font-size: 0.85rem; color: #464555;">Dữ liệu {total_customers:,} khách hàng đã được phân thành {num_clusters} phân khúc kinh doanh rõ nét.</div>
                </div>
            </div>
            <div style="display: flex; gap: 10px;">
                <div class="ci-stat-box" style="padding: 6px 14px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">{total_customers:,}</div>
                    <div style="font-size: 9px; font-weight: 600; color: #464555; text-transform: uppercase;">Khách hàng</div>
                </div>
                <div class="ci-stat-box" style="padding: 6px 14px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">{num_clusters}</div>
                    <div style="font-size: 9px; font-weight: 600; color: #464555; text-transform: uppercase;">Phân khúc</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- CLUSTER PROFILE CARDS ---
    st.markdown(
        """
        <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            Tổng quan các phân khúc khách hàng
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_cols = st.columns(min(num_clusters, 3), gap="medium")
    for i, (_, row) in enumerate(current_profile.iterrows()):
        col = card_cols[i % len(card_cols)]
        c_id = int(row["Cluster"])
        color = CLUSTER_PALETTE[c_id % len(CLUSTER_PALETTE)]
        count = int(row["count"])
        pct = float(row["percentage"]) if "percentage" in row else (float(count) / total_customers * 100.0 if total_customers else 0.0)
        name = str(row["SegmentName"])

        with col:
            st.markdown(
                f"""
                <div class="ci-profile-card" style="border-top: 4px solid {color}; margin-bottom: 16px;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <div style="width: 10px; height: 10px; border-radius: 50%; background: {color};"></div>
                                <span style="font-size: 1rem; font-weight: 700; color: #0b1c30;">Cluster {c_id + 1:02d}</span>
                            </div>
                            <span style="font-size: 11px; font-weight: 600; color: #464555;">{count:,} KH ({pct:.1f}%)</span>
                        </div>
                        <div style="font-size: 0.88rem; font-weight: 700; color: #3525cd; min-height: 38px; margin-bottom: 12px;">
                            {name}
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4px; border-top: 1px solid #eff4ff; padding-top: 10px; text-align: center;">
                            <div>
                                <div style="font-size: 9px; color: #464555; text-transform: uppercase; font-weight: 600;">Mean R</div>
                                <div style="font-size: 0.95rem; font-weight: 700; color: #0b1c30;">{row['mean Recency']:.2f}</div>
                            </div>
                            <div>
                                <div style="font-size: 9px; color: #464555; text-transform: uppercase; font-weight: 600;">Mean F</div>
                                <div style="font-size: 0.95rem; font-weight: 700; color: #0b1c30;">{row['mean Frequency']:.2f}</div>
                            </div>
                            <div>
                                <div style="font-size: 9px; color: #464555; text-transform: uppercase; font-weight: 600;">Mean M</div>
                                <div style="font-size: 0.95rem; font-weight: 700; color: #0b1c30;">{row['mean Monetary']:.2f}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # --- SEGMENT 360 & RFM COMPARISON (2 COLUMNS) ---
    col_s360, col_rfm_comp = st.columns([1.2, 1.8], gap="large")

    with col_s360:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
                    Chi tiết phân khúc (Segment 360)
                </div>
            """,
            unsafe_allow_html=True,
        )
        seg_options = ["Tất cả"] + [f"Cluster {int(r['Cluster']) + 1:02d}" for _, r in current_profile.iterrows()]
        selected_seg = st.selectbox("Chọn phân khúc để xem chi tiết", seg_options, key="seg_360_select")

        if selected_seg == "Tất cả":
            st.markdown(
                f"""
                <div style="padding-top: 10px;">
                    <div style="font-size: 1rem; font-weight: 700; color: #0b1c30; margin-bottom: 4px;">Tổng quan toàn bộ tệp khách hàng</div>
                    <p style="font-size: 0.88rem; color: #464555; line-height: 1.5; margin-bottom: 12px;">
                        Bao gồm <strong>{total_customers:,}</strong> khách hàng đã qua tiền xử lý chuẩn hóa và phân cụm K-Means.
                    </p>
                    <div style="background: #f8f9ff; border: 1px solid #dce9ff; border-radius: 8px; padding: 12px; font-size: 0.82rem; color: #464555;">
                        Chọn từng Cluster trong danh sách trên để xem chi tiết đặc tính Recency, Frequency và Monetary trung bình của phân khúc đó.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            c_idx = int(selected_seg.replace("Cluster ", "")) - 1
            matching_rows = current_profile[current_profile["Cluster"] == c_idx]
            if not matching_rows.empty:
                s_row = matching_rows.iloc[0]
                s_color = CLUSTER_PALETTE[c_idx % len(CLUSTER_PALETTE)]
                s_count = int(s_row["count"])
                s_pct = float(s_row["percentage"]) if "percentage" in s_row else (float(s_count) / total_customers * 100.0 if total_customers else 0.0)
                st.markdown(
                    f"""
                    <div style="padding-top: 6px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <div style="width: 12px; height: 12px; border-radius: 50%; background: {s_color};"></div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">{selected_seg} (Model ID: {c_idx})</div>
                        </div>
                        <div style="font-size: 0.9rem; font-weight: 700; color: #3525cd; margin-bottom: 12px;">
                            {s_row['SegmentName']}
                        </div>
                        <div style="background: #f8f9ff; border: 1px solid #dce9ff; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px; font-size: 0.85rem;">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: #464555;">Quy mô:</span>
                                <strong>{s_count:,} KH ({s_pct:.1f}%)</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: #464555;">Recency trung bình:</span>
                                <strong>{s_row['mean Recency']:.2f}</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: #464555;">Frequency trung bình:</span>
                                <strong>{s_row['mean Frequency']:.2f}</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: #464555;">Monetary trung bình:</span>
                                <strong>{s_row['mean Monetary']:.2f}</strong>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_rfm_comp:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
                    So sánh RFM giữa các phân khúc
                </div>
            """,
            unsafe_allow_html=True,
        )

        tab_r, tab_f, tab_m = st.tabs(["Recency (R)", "Frequency (F)", "Monetary (M)"])

        plot_df = current_profile.copy()
        plot_df["ClusterLabel"] = plot_df["Cluster"].apply(lambda c: f"Cluster {int(c) + 1:02d}")

        with tab_r:
            st.caption("Recency trung bình: Thấp hơn = mua gần đây hơn")
            fig_r = px.bar(
                plot_df,
                x="ClusterLabel",
                y="mean Recency",
                color="ClusterLabel",
                color_discrete_sequence=CLUSTER_PALETTE[:num_clusters],
                text_auto=".2f",
            )
            fig_r.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=220,
                showlegend=False,
                plot_bgcolor="rgba(248, 249, 255, 0.6)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=11),
                xaxis=dict(title=None),
                yaxis=dict(title="Mean Recency"),
            )
            st.plotly_chart(fig_r, width="stretch")

        with tab_f:
            st.caption("Frequency trung bình: Cao hơn = mua thường xuyên hơn")
            fig_f = px.bar(
                plot_df,
                x="ClusterLabel",
                y="mean Frequency",
                color="ClusterLabel",
                color_discrete_sequence=CLUSTER_PALETTE[:num_clusters],
                text_auto=".2f",
            )
            fig_f.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=220,
                showlegend=False,
                plot_bgcolor="rgba(248, 249, 255, 0.6)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=11),
                xaxis=dict(title=None),
                yaxis=dict(title="Mean Frequency"),
            )
            st.plotly_chart(fig_f, width="stretch")

        with tab_m:
            st.caption("Monetary trung bình: Cao hơn = giá trị giao dịch lớn hơn")
            fig_m = px.bar(
                plot_df,
                x="ClusterLabel",
                y="mean Monetary",
                color="ClusterLabel",
                color_discrete_sequence=CLUSTER_PALETTE[:num_clusters],
                text_auto=".2f",
            )
            fig_m.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=220,
                showlegend=False,
                plot_bgcolor="rgba(248, 249, 255, 0.6)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=11),
                xaxis=dict(title=None),
                yaxis=dict(title="Mean Monetary"),
            )
            st.plotly_chart(fig_m, width="stretch")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- CUSTOMER EXPLORER ---
    st.subheader("Khám phá khách hàng")

    col_flt1, col_flt2 = st.columns([1, 2], gap="medium")
    with col_flt1:
        cluster_filter_options = ["Tất cả phân khúc"] + [
            f"Cluster {int(r['Cluster']) + 1:02d}" for _, r in current_profile.iterrows()
        ]
        selected_cluster_filter = st.selectbox(
            "Lọc theo phân khúc",
            cluster_filter_options,
            key="customer_cluster_filter",
        )
    with col_flt2:
        query = st.text_input("Tìm CustomerID", key="tv6_customer_query")

    # Apply Filters
    visible = customers
    if selected_cluster_filter != "Tất cả phân khúc":
        filter_cluster_idx = int(selected_cluster_filter.replace("Cluster ", "")) - 1
        visible = visible[visible["Cluster"] == filter_cluster_idx]

    if query.strip():
        visible = visible[
            visible["CustomerID"].astype(str).str.contains(query.strip(), case=False, regex=False)
        ]

    st.caption(f"Hiển thị {len(visible):,} / {total_customers:,} khách hàng (Dữ liệu RFM gốc)")
    st.dataframe(visible, width="stretch", hide_index=True)

    # --- CLUSTER PROFILES TABLE ---
    st.subheader("Hồ sơ cụm")
    st.dataframe(current_profile, width="stretch", hide_index=True)

    # --- CUSTOMER 360 DRILL-DOWN ---
    if not visible.empty:
        with st.expander("So sánh chi tiết một khách hàng cụ thể (Customer 360)", expanded=False):
            cust_list = list(visible["CustomerID"].astype(str))
            selected_cid = st.selectbox("Chọn CustomerID để kiểm tra:", cust_list, key="c360_cid_select")
            c_row = customers[customers["CustomerID"].astype(str) == selected_cid].iloc[0]
            c_cluster = int(c_row["Cluster"])
            c_color = CLUSTER_PALETTE[c_cluster % len(CLUSTER_PALETTE)]
            c_prof = current_profile[current_profile["Cluster"] == c_cluster].iloc[0]

            st.markdown(
                f"""
                <div style="background: #ffffff; border: 1px solid #dce9ff; border-radius: 10px; padding: 16px; margin-top: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">Khách hàng: {selected_cid}</div>
                        <span style="background: {c_color}18; color: {c_color}; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 9999px;">
                            Cluster {c_cluster + 1:02d} (Model ID: {c_cluster})
                        </span>
                    </div>
                    <div style="font-size: 0.9rem; color: #3525cd; font-weight: 600; margin-bottom: 14px;">
                        Phân khúc: {c_row['SegmentName']}
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; text-align: center;">
                        <div class="ci-stat-box">
                            <div style="font-size: 10px; color: #464555; text-transform: uppercase; font-weight: 600;">Recency (Gốc)</div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">{c_row['Recency']}</div>
                            <div style="font-size: 10px; color: #464555; margin-top: 2px;">TB Cụm: {c_prof['mean Recency']:.2f}</div>
                        </div>
                        <div class="ci-stat-box">
                            <div style="font-size: 10px; color: #464555; text-transform: uppercase; font-weight: 600;">Frequency (Gốc)</div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">{c_row['Frequency']}</div>
                            <div style="font-size: 10px; color: #464555; margin-top: 2px;">TB Cụm: {c_prof['mean Frequency']:.2f}</div>
                        </div>
                        <div class="ci-stat-box">
                            <div style="font-size: 10px; color: #464555; text-transform: uppercase; font-weight: 600;">Monetary (Gốc)</div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">{c_row['Monetary']}</div>
                            <div style="font-size: 10px; color: #464555; margin-top: 2px;">TB Cụm: {c_prof['mean Monetary']:.2f}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

    # --- EXPORT CENTER & MODEL METADATA / INTEGRITY (2 COLUMNS) ---
    col_export, col_meta = st.columns([1.2, 1.2], gap="large")

    with col_export:
        st.markdown(
            f"""
            <div class="ci-card" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h3 style="font-size: 1.1rem; font-weight: 700; color: #0b1c30; margin-bottom: 4px;">Xuất kết quả phân cụm</h3>
                    <p style="font-size: 0.88rem; color: #464555; margin-bottom: 14px;">
                        Tải tệp CSV chứa danh sách toàn bộ {total_customers:,} khách hàng với gán cụm và nhãn phân đoạn kinh doanh.
                    </p>
                    <div style="background: #f8f9ff; border: 1px solid #dce9ff; border-radius: 8px; padding: 10px 14px; margin-bottom: 14px; display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 20px;">📄</span>
                        <div>
                            <div style="font-size: 0.9rem; font-weight: 700; color: #0b1c30;">customer_results.csv</div>
                            <div style="font-size: 0.78rem; color: #464555;">Định dạng chuẩn CSV, mã hóa UTF-8 BOM, 6 cột dữ liệu</div>
                        </div>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "Tải CSV kết quả khách hàng",
            data=customer_results_to_csv_bytes(customers),
            file_name="customer_results.csv",
            mime="text/csv",
            key="tv6_customer_export",
            type="primary",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_meta:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
                    Thông tin mô hình & Kiểm tra toàn vẹn
                </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader("Thông tin lần chạy")
        st.json(current_metadata)

        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.85rem; margin-top: 10px;">
                <div style="display: flex; align-items: center; gap: 8px; color: #006a61;">
                    <span>✓</span> <span><strong>{total_customers:,}/{total_customers:,}</strong> khách hàng đã được phân cụm thành công</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px; color: #006a61;">
                    <span>✓</span> <span>Mã <strong>CustomerID</strong> duy nhất được bảo toàn nguyên vẹn</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px; color: #006a61;">
                    <span>✓</span> <span>Không có giá trị <strong>Cluster</strong> hoặc <strong>SegmentName</strong> bị thiếu</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px; color: #006a61;">
                    <span>✓</span> <span>Bộ dữ liệu RFM gốc được bảo toàn trong kết quả cuối</span>
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


render_results_page(_page_state())
