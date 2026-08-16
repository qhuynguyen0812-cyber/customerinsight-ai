"""Trang Phân cụm khách hàng bằng thuật toán K-Means."""

import streamlit as st
import streamlit.components.v1 as components

from components.states import get_app_state
from components.theme import apply_custom_theme
from components.workflow import consume_flash, set_flash
from src.clustering import get_default_solver_kwargs
from src.profiling import run_clustering_workflow

CLUSTER_PALETTE = [
    "#3525cd",  # Cluster 0 / 01: Primary Indigo
    "#006a61",  # Cluster 1 / 02: Secondary Teal
    "#8b5cf6",  # Cluster 2 / 03: Accent Violet
    "#2563eb",  # Cluster 3 / 04: Blue
    "#059669",  # Cluster 4 / 05: Emerald
    "#d97706",  # Cluster 5 / 06: Amber
    "#dc2626",  # Cluster 6 / 07: Red
]


def render_conceptual_animation(k: int, iterations: int) -> None:
    """Render an isolated client-side conceptual clustering visualization."""
    num_k = max(2, min(k, 7))
    palette_json = str(CLUSTER_PALETTE[:num_k]).replace("'", '"')

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            body {{ background: transparent; overflow: hidden; }}
            .container {{
                background: #ffffff;
                border: 1px solid #e2dfff;
                border-radius: 12px;
                padding: 16px;
                display: flex;
                flex-direction: column;
                height: 380px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }}
            .title {{
                font-size: 13px;
                font-weight: 700;
                color: #0b1c30;
            }}
            .subtitle {{
                font-size: 11px;
                color: #464555;
                margin-top: 2px;
            }}
            .tracker {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 11px;
            }}
            .tracker-step {{
                display: flex;
                align-items: center;
                gap: 4px;
                color: #464555;
                opacity: 0.6;
                transition: all 0.3s ease;
            }}
            .tracker-step.active {{
                color: #3525cd;
                font-weight: 700;
                opacity: 1;
            }}
            .tracker-dot {{
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: currentColor;
            }}
            .canvas-wrap {{
                flex: 1;
                background: #f8f9ff;
                border: 1px solid #dce9ff;
                border-radius: 8px;
                position: relative;
                overflow: hidden;
            }}
            .point {{
                position: absolute;
                width: 7px;
                height: 7px;
                border-radius: 50%;
                transform: translate(-50%, -50%);
                transition: all 1.2s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            .centroid {{
                position: absolute;
                width: 18px;
                height: 18px;
                border-radius: 4px;
                background: #ffffff;
                border: 3px solid #3525cd;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                transform: translate(-50%, -50%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 9px;
                z-index: 10;
                transition: all 1.2s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            @media (prefers-reduced-motion: reduce) {{
                .point, .centroid {{ transition: none !important; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <div class="title" id="viz-title">Hội tụ hoàn tất · {iterations} lần lặp</div>
                    <div class="subtitle">Minh họa trực quan · kết quả mô hình được tính trên dữ liệu RFM chuẩn hóa.</div>
                </div>
                <div class="tracker" id="tracker">
                    <div class="tracker-step" id="t0"><span class="tracker-dot"></span> Khởi tạo</div>
                    <span style="color:#dce9ff;">-</span>
                    <div class="tracker-step" id="t1"><span class="tracker-dot"></span> Gán cụm</div>
                    <span style="color:#dce9ff;">-</span>
                    <div class="tracker-step" id="t2"><span class="tracker-dot"></span> Cập nhật</div>
                    <span style="color:#dce9ff;">-</span>
                    <div class="tracker-step active" id="t3"><span class="tracker-dot"></span> Hội tụ</div>
                </div>
            </div>
            <div class="canvas-wrap" id="canvas-area"></div>
        </div>

        <script>
            (function() {{
                const k = {num_k};
                const colors = {palette_json};
                const area = document.getElementById('canvas-area');
                const isReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

                // Define synthetic cluster centers around canvas
                const centers = [];
                for (let i = 0; i < k; i++) {{
                    const angle = (i / k) * 2 * Math.PI - Math.PI / 2;
                    const r = 32;
                    centers.push({{
                        x: 50 + r * Math.cos(angle),
                        y: 50 + r * Math.sin(angle)
                    }});
                }}

                // Generate synthetic points
                const points = [];
                const totalPoints = 120;
                for (let i = 0; i < totalPoints; i++) {{
                    const cIdx = i % k;
                    const center = centers[cIdx];
                    const angle = Math.random() * 2 * Math.PI;
                    const dist = Math.random() * 14;
                    const fx = Math.max(8, Math.min(92, center.x + dist * Math.cos(angle)));
                    const fy = Math.max(8, Math.min(92, center.y + dist * Math.sin(angle)));
                    points.push({{
                        cIdx: cIdx,
                        fx: fx,
                        fy: fy,
                        ix: 50 + (Math.random() - 0.5) * 60,
                        iy: 50 + (Math.random() - 0.5) * 60
                    }});
                }}

                function setTracker(step) {{
                    for (let s = 0; s <= 3; s++) {{
                        const el = document.getElementById('t' + s);
                        if (el) {{
                            if (s === step) el.className = 'tracker-step active';
                            else el.className = 'tracker-step';
                        }}
                    }}
                }}

                if (isReduced) {{
                    // Render static converged state directly
                    points.forEach((p, idx) => {{
                        const pt = document.createElement('div');
                        pt.className = 'point';
                        pt.style.left = p.fx + '%';
                        pt.style.top = p.fy + '%';
                        pt.style.backgroundColor = colors[p.cIdx];
                        pt.style.opacity = '0.75';
                        area.appendChild(pt);
                    }});
                    centers.forEach((c, idx) => {{
                        const ct = document.createElement('div');
                        ct.className = 'centroid';
                        ct.style.left = c.x + '%';
                        ct.style.top = c.y + '%';
                        ct.style.borderColor = colors[idx];
                        ct.style.color = colors[idx];
                        ct.textContent = 'C' + (idx + 1);
                        area.appendChild(ct);
                    }});
                    setTracker(3);
                    return;
                }}

                // Animation Sequence
                setTracker(0);
                points.forEach((p, idx) => {{
                    const pt = document.createElement('div');
                    pt.id = 'pt-' + idx;
                    pt.className = 'point';
                    pt.style.left = p.ix + '%';
                    pt.style.top = p.iy + '%';
                    pt.style.backgroundColor = '#94a3b8';
                    pt.style.opacity = '0.5';
                    area.appendChild(pt);
                }});

                setTimeout(() => {{
                    setTracker(1);
                    // Add centroids
                    centers.forEach((c, idx) => {{
                        const ct = document.createElement('div');
                        ct.id = 'ct-' + idx;
                        ct.className = 'centroid';
                        ct.style.left = '50%';
                        ct.style.top = '50%';
                        ct.style.borderColor = colors[idx];
                        ct.style.color = colors[idx];
                        ct.textContent = 'C' + (idx + 1);
                        area.appendChild(ct);
                    }});

                    setTimeout(() => {{
                        setTracker(2);
                        // Move centroids & color points
                        centers.forEach((c, idx) => {{
                            const ct = document.getElementById('ct-' + idx);
                            if (ct) {{
                                ct.style.left = c.x + '%';
                                ct.style.top = c.y + '%';
                            }}
                        }});
                        points.forEach((p, idx) => {{
                            const pt = document.getElementById('pt-' + idx);
                            if (pt) {{
                                pt.style.left = p.fx + '%';
                                pt.style.top = p.fy + '%';
                                pt.style.backgroundColor = colors[p.cIdx];
                                pt.style.opacity = '0.75';
                            }}
                        }});

                        setTimeout(() => {{
                            setTracker(3);
                        }}, 1200);
                    }}, 600);
                }}, 400);
            }})();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=395)


def render_page() -> None:
    """Main render function for Step 4: K-Means Clustering & Profiling."""
    apply_custom_theme()
    state = get_app_state()

    # --- HEADER ---
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <span class="ci-badge">BƯỚC 04 · PHÂN CỤM</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("Phân cụm khách hàng với K-Means")
    st.markdown(
        """
        <p style="font-size: 1.02rem; color: #464555; margin-bottom: 24px; max-width: 800px;">
            Huấn luyện mô hình K-Means với số cụm K đã xác nhận và phân tích hồ sơ phân khúc.
        </p>
        """,
        unsafe_allow_html=True,
    )

    flash = consume_flash(st.session_state)
    if flash is not None:
        getattr(st, flash.level, st.info)(flash.text)

    # --- GATING CHECKS ---
    if state.scaled_matrix is None:
        st.info("Hãy hoàn thành bước tiền xử lý dữ liệu trước khi phân cụm.")
        st.stop()

    if state.selected_k is None:
        st.info("Hãy phân tích và xác nhận K trước khi chạy K-Means.")
        st.stop()

    # --- SOLVER CONFIGURATION & RUN ACTION ---
    solver = get_default_solver_kwargs()
    if isinstance(state.solver_preferences, dict):
        solver.update(state.solver_preferences)

    st.markdown(
        f"""
        <div class="ci-banner" style="margin-bottom: 24px;">
            <div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #0b1c30; margin-bottom: 4px;">
                    Cấu hình mô hình K-Means
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; font-size: 0.82rem; color: #464555;">
                    <span class="ci-chip">K = <strong>{state.selected_k}</strong></span>
                    <span class="ci-chip">init: <strong>{solver['init']}</strong></span>
                    <span class="ci-chip">n_init: <strong>{solver['n_init']}</strong></span>
                    <span class="ci-chip">random_state: <strong>{solver['random_state']}</strong></span>
                    <span class="ci-chip">max_iter: <strong>{solver['max_iter']}</strong></span>
                    <span class="ci-chip">tol: <strong>{solver['tol']}</strong></span>
                </div>
            </div>
            <div class="ci-stat-box" style="padding: 6px 16px;">
                <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">{len(state.scaled_matrix):,}</div>
                <div style="font-size: 9px; font-weight: 600; color: #464555; text-transform: uppercase;">Khách hàng</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Chạy K-Means", type="primary", use_container_width=True):
        try:
            run_clustering_workflow(state)
        except (TypeError, ValueError) as exc:
            st.error(f"Không thể hoàn thành phân cụm: {exc}")
        else:
            set_flash(st.session_state, "Đã hoàn thành phân cụm và lập hồ sơ khách hàng.")
            st.rerun()

    if state.cluster_profiles is None or state.run_metadata is None:
        st.info("Nhấn **Chạy K-Means** ở trên để bắt đầu phân cụm và tạo hồ sơ khách hàng.")
        st.stop()

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # --- SUMMARY & DETAILS (2 COLUMNS) ---
    profiles = state.cluster_profiles
    meta = state.run_metadata
    total_customers = int(profiles["count"].sum())
    num_clusters = len(profiles)

    # Find largest cluster
    largest_row = profiles.loc[profiles["count"].idxmax()]
    largest_cluster_id = int(largest_row["Cluster"]) + 1
    largest_pct = float(largest_row["percentage"])

    col_sum, col_det = st.columns([1.6, 1.2], gap="large")
    with col_sum:
        st.markdown(
            f"""
            <div class="ci-card" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <span style="color: #3525cd; font-size: 14px;">✦</span>
                        <div style="font-size: 11px; font-weight: 700; color: #3525cd; text-transform: uppercase; letter-spacing: 0.06em;">
                            Tóm tắt phân cụm
                        </div>
                    </div>
                    <p style="font-size: 0.92rem; color: #464555; line-height: 1.6; margin: 0;">
                        <strong>{total_customers:,}</strong> khách hàng đã được phân thành <strong>{num_clusters}</strong> phân khúc rõ rệt.
                        Cluster {largest_cluster_id:02d} là nhóm lớn nhất chiếm <strong>{largest_pct:.1f}%</strong> khách hàng.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_det:
        with st.expander("Chi tiết lần chạy (Run Metadata)", expanded=False):
            st.markdown(
                f"""
                <div style="font-size: 0.85rem; color: #0b1c30; display: flex; flex-direction: column; gap: 6px;">
                    <div style="display: flex; justify-content: space-between;"><span>Số cụm (K):</span> <strong>{meta['k']}</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span>Inertia:</span> <strong>{meta['inertia']:.4f}</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span>Silhouette Score:</span> <strong>{meta['silhouette']:.4f}</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span>Số lần lặp (Iterations):</span> <strong>{meta['iterations']}</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span>Thời gian chạy (Runtime):</span> <strong>{meta['runtime_seconds']:.4f} s</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- BENTO GRID: VISUALIZATION & METRICS / DISTRIBUTION ---
    col_viz, col_metrics = st.columns([1.6, 1.2], gap="large")

    with col_viz:
        render_conceptual_animation(state.selected_k, meta["iterations"])

    with col_metrics:
        # Post-Run Metrics Cards
        st.markdown(
            f"""
            <div class="ci-card" style="margin-bottom: 16px;">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
                    Chỉ số sau khi chạy
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                    <div class="ci-stat-box">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #0b1c30;">{total_customers:,}</div>
                        <div style="font-size: 9px; font-weight: 600; color: #464555; text-transform: uppercase;">Khách hàng</div>
                    </div>
                    <div class="ci-stat-box">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #0b1c30;">{num_clusters}</div>
                        <div style="font-size: 9px; font-weight: 600; color: #464555; text-transform: uppercase;">Phân khúc (K)</div>
                    </div>
                    <div class="ci-stat-box">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #0b1c30;">{meta['iterations']}</div>
                        <div style="font-size: 9px; font-weight: 600; color: #464555; text-transform: uppercase;">Lần lặp</div>
                    </div>
                    <div class="ci-stat-box">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #006a61;">{meta['silhouette']:.4f}</div>
                        <div style="font-size: 9px; font-weight: 600; color: #006a61; text-transform: uppercase;">Silhouette</div>
                    </div>
                    <div class="ci-stat-box" style="grid-column: span 2; display: flex; justify-content: space-between; align-items: center; padding: 8px 14px;">
                        <div style="font-size: 10px; font-weight: 600; color: #464555; text-transform: uppercase;">Inertia</div>
                        <div style="font-size: 1.05rem; font-weight: 700; color: #0b1c30;">{meta['inertia']:.4f}</div>
                    </div>
                </div>
                <div style="text-align: right; font-size: 11px; color: #464555; padding-top: 4px; border-top: 1px solid #eff4ff;">
                    Runtime: <strong style="color: #0b1c30;">{meta['runtime_seconds']:.4f} s</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Distribution Bars
        st.markdown(
            """
            <div class="ci-card">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
                    Phân bổ phân khúc
                </div>
            """,
            unsafe_allow_html=True,
        )
        for idx, row in profiles.iterrows():
            c_idx = int(row["Cluster"])
            color = CLUSTER_PALETTE[c_idx % len(CLUSTER_PALETTE)]
            count = int(row["count"])
            pct = float(row["percentage"])
            st.markdown(
                f"""
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: {color};">Cluster {c_idx + 1:02d} ({pct:.1f}%)</span>
                        <span style="color: #464555; font-weight: 600;">{count:,} KH</span>
                    </div>
                    <div style="width: 100%; height: 6px; background: #eff4ff; border-radius: 9999px; overflow: hidden;">
                        <div style="width: {pct}%; height: 100%; background: {color}; border-radius: 9999px;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- PROFILE CARDS (HỒ SƠ PHÂN KHÚC) ---
    st.markdown(
        """
        <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 14px;">
            Hồ sơ phân khúc khách hàng
        </div>
        """,
        unsafe_allow_html=True,
    )

    prof_cols = st.columns(min(len(profiles), 3), gap="medium")
    for i, (_, row) in enumerate(profiles.iterrows()):
        col = prof_cols[i % len(prof_cols)]
        c_idx = int(row["Cluster"])
        color = CLUSTER_PALETTE[c_idx % len(CLUSTER_PALETTE)]
        count = int(row["count"])
        pct = float(row["percentage"])
        seg_name = str(row["SegmentName"])

        with col:
            st.markdown(
                f"""
                <div class="ci-profile-card" style="border-top: 4px solid {color}; margin-bottom: 16px;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <div style="width: 10px; height: 10px; border-radius: 50%; background: {color};"></div>
                                <span style="font-size: 1rem; font-weight: 700; color: #0b1c30;">Cluster {c_idx + 1:02d}</span>
                            </div>
                            <span style="font-size: 11px; font-weight: 600; color: #464555;">{count:,} KH ({pct:.1f}%)</span>
                        </div>
                        <div style="font-size: 0.88rem; font-weight: 700; color: #3525cd; min-height: 40px; margin-bottom: 14px;">
                            {seg_name}
                        </div>
                        <div style="font-size: 0.82rem; color: #464555; display: flex; flex-direction: column; gap: 6px; border-top: 1px solid #eff4ff; padding-top: 10px;">
                            <div style="display: flex; justify-content: space-between;">
                                <span>Recency TB (R):</span>
                                <strong style="color: #0b1c30;">{row['mean Recency']:.2f}</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span>Frequency TB (F):</span>
                                <strong style="color: #0b1c30;">{row['mean Frequency']:.2f}</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span>Monetary TB (M):</span>
                                <strong style="color: #0b1c30;">{row['mean Monetary']:.2f}</strong>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- NEXT STEP CTA ---
    st.markdown(
        """
        <div class="ci-banner">
            <div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #0b1c30; margin-bottom: 2px;">
                    Kết quả phân khúc đã sẵn sàng
                </div>
                <div style="font-size: 0.85rem; color: #464555;">
                    Khám phá từng khách hàng, so sánh chi tiết hồ sơ phân khúc và xuất dữ liệu ở bước tiếp theo.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_cta_pad, col_cta_btn = st.columns([1, 1])
    with col_cta_btn:
        if st.button("Tiếp tục: Xem kết quả →", type="primary", use_container_width=True):
            st.switch_page("views/5_Ket_qua.py")
        st.caption("Bước tiếp theo: Phân tích kết quả chi tiết, tìm kiếm khách hàng và xuất báo cáo CSV")


render_page()
