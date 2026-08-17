"""Trang Dữ liệu: Nạp/Tải dữ liệu khách hàng, kiểm tra hợp lệ và hiển thị chất lượng."""

from pathlib import Path

import pandas as pd
import streamlit as st

from components.states import get_app_state
from components.theme import apply_custom_theme
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


def render_quality_section(raw_df: pd.DataFrame) -> None:
    """Render validation checklist, quality table, and assessment based on real data."""
    report = build_quality_report(raw_df)
    total_missing = sum(report.missing_by_column[k] for k in ("Recency", "Frequency", "Monetary"))
    total_outliers = sum(report.iqr_outlier_by_column.values())

    col_check, col_table = st.columns([1, 2], gap="large")

    with col_check:
        st.markdown(
            """
            <div class="ci-card" style="height: 100%;">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 16px;">
                    Kiểm tra dữ liệu
                </div>
                <div style="display: flex; flex-direction: column; gap: 12px; font-size: 0.9rem; color: #0b1c30;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #006a61; font-weight: bold; font-size: 16px;">✓</span>
                        <span>Đọc cấu trúc tệp CSV</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #006a61; font-weight: bold; font-size: 16px;">✓</span>
                        <span>Kiểm tra các cột bắt buộc</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #006a61; font-weight: bold; font-size: 16px;">✓</span>
                        <span>Kiểm tra kiểu dữ liệu số</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #006a61; font-weight: bold; font-size: 16px;">✓</span>
                        <span>Kiểm tra tính duy nhất CustomerID</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #006a61; font-weight: bold; font-size: 16px;">✓</span>
                        <span>Đánh giá chất lượng RFM</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_table:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="font-size: 11px; font-weight: 700; color: #0b1c30; text-transform: uppercase; letter-spacing: 0.06em;">
                    Chất lượng dữ liệu RFM
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        quality_rows = []
        for feat in ("Recency", "Frequency", "Monetary"):
            missing_count = report.missing_by_column.get(feat, 0)
            missing_pct = (missing_count / report.row_count * 100.0) if report.row_count else 0.0
            outlier_count = report.iqr_outlier_by_column.get(feat, 0)
            outlier_pct = (outlier_count / report.row_count * 100.0) if report.row_count else 0.0
            status = "✓ Hợp lệ" if missing_count == 0 else "⚠ Có giá trị thiếu"
            quality_rows.append(
                {
                    "Thuộc tính": feat,
                    "Giá trị thiếu": f"{missing_count} ({missing_pct:.1f}%)",
                    "Ngoại lệ (IQR)": f"{outlier_count} ({outlier_pct:.1f}%)",
                    "Trạng thái": status,
                }
            )

        st.dataframe(pd.DataFrame(quality_rows), width="stretch", hide_index=True)

        if report.zero_variance_columns:
            st.warning("Cột không có độ biến thiên: " + ", ".join(report.zero_variance_columns))

        # Assessment Box
        missing_text = (
            "✓ Không có giá trị RFM còn thiếu"
            if total_missing == 0
            else f"⚠ {total_missing} giá trị RFM còn thiếu (sẽ được xử lý bằng Median Imputation)"
        )
        outlier_text = (
            f"ℹ {total_outliers} giá trị ngoại lệ theo IQR (sẽ được xử lý ở bước tiền xử lý)"
            if total_outliers > 0
            else "✓ Không phát hiện ngoại lệ theo IQR"
        )

        st.markdown(
            f"""
            <div class="ci-assessment-box" style="margin-top: 16px;">
                <div style="font-size: 11px; font-weight: 700; color: #3525cd; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;">
                    ✦ ĐÁNH GIÁ DỮ LIỆU
                </div>
                <div style="font-size: 0.92rem; font-weight: 600; color: #0b1c30; margin-bottom: 6px;">
                    Sẵn sàng cho bước Khám phá & Tiền xử lý
                </div>
                <div style="font-size: 0.85rem; color: #464555; line-height: 1.6; margin-bottom: 8px;">
                    <div>✓ {report.row_count:,} khách hàng với CustomerID hợp lệ và duy nhất</div>
                    <div>{missing_text}</div>
                    <div>{outlier_text}</div>
                </div>
                <div style="font-size: 0.83rem; color: #3525cd; font-weight: 500;">
                    Tiếp tục sang bước Khám phá dữ liệu để phân tích phân phối và tiến hành làm sạch, chuẩn hóa.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_page() -> None:
    """Main render entrypoint for the Data preparation page."""
    apply_custom_theme()

    # --- HEADER ---
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <span class="ci-badge">BƯỚC 01 · DỮ LIỆU</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("Chuẩn bị dữ liệu khách hàng")
    st.markdown(
        """
        <p style="font-size: 1.02rem; color: #464555; margin-bottom: 24px; max-width: 800px;">
            Bắt đầu với bộ dữ liệu mẫu hoặc tải lên dữ liệu RFM của riêng bạn. Hệ thống sẽ kiểm tra cấu trúc và chất lượng trước khi phân tích.
        </p>
        """,
        unsafe_allow_html=True,
    )

    flash = consume_flash(st.session_state)
    if flash is not None:
        getattr(st, flash.level, st.info)(flash.text)

    # --- SOURCE SELECTION AREA (2 CARDS) ---
    sample_col, upload_col = st.columns(2, gap="large")

    with sample_col:
        st.markdown(
            """
            <div class="ci-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin-bottom: 4px;">
                            Bộ dữ liệu RFM của dự án
                        </h3>
                        <p style="font-size: 0.85rem; color: #464555; margin: 0;">
                            Dataset mẫu tích hợp sẵn của nhóm
                        </p>
                    </div>
                    <span style="background: #e5eeff; color: #3525cd; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 6px; text-transform: uppercase;">
                        CSV
                    </span>
                </div>
                <div style="display: flex; gap: 24px; margin-bottom: 16px;">
                    <div>
                        <div style="font-size: 11px; color: #464555; text-transform: uppercase; font-weight: 500;">Quy mô</div>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #0b1c30;">720 khách hàng</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #464555; text-transform: uppercase; font-weight: 500;">Cấu trúc</div>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #0b1c30;">4 thuộc tính</div>
                    </div>
                </div>
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 11px; color: #464555; text-transform: uppercase; font-weight: 500; margin-bottom: 8px;">Trường dữ liệu</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                        <span class="ci-chip" style="font-size: 11px; padding: 4px 10px;">CustomerID</span>
                        <span class="ci-chip" style="font-size: 11px; padding: 4px 10px;">Recency</span>
                        <span class="ci-chip" style="font-size: 11px; padding: 4px 10px;">Frequency</span>
                        <span class="ci-chip" style="font-size: 11px; padding: 4px 10px;">Monetary</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Dùng dataset mẫu", type="primary", use_container_width=True):
            try:
                result = load_sample_dataset(SAMPLE_PATH)
            except DataValidationError as exc:
                st.error(str(exc))
            else:
                commit_validated(result)

    with upload_col:
        st.markdown(
            """
            <div class="ci-card">
                <div style="margin-bottom: 12px;">
                    <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin-bottom: 4px;">
                        Tải dữ liệu của bạn
                    </h3>
                    <p style="font-size: 0.85rem; color: #464555; margin: 0;">
                        Tải lên tệp CSV có 4 cột: CustomerID, Recency, Frequency, Monetary.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "Chọn file CSV",
            type=["csv"],
            help="Tệp CSV cần có các cột: CustomerID, Recency, Frequency, Monetary",
            label_visibility="collapsed",
        )
        if st.button(
            "Kiểm tra và sử dụng CSV",
            disabled=uploaded is None,
            use_container_width=True,
        ):
            try:
                result = load_csv_bytes(uploaded.getvalue())
            except DataValidationError as exc:
                st.error(str(exc))
            else:
                commit_validated(result)

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # --- DATASET STATUS / QUALITY / PREVIEW ---
    state = get_app_state()

    if state.raw_df is None:
        st.markdown(
            """
            <div class="ci-card" style="text-align: center; padding: 36px 20px;">
                <div style="font-size: 32px; margin-bottom: 10px;">📊</div>
                <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin-bottom: 6px;">
                    Chưa có dataset hợp lệ nào đang hoạt động
                </h3>
                <p style="font-size: 0.9rem; color: #464555; max-width: 480px; margin: 0 auto;">
                    Hãy chọn <strong>Dùng dataset mẫu</strong> hoặc <strong>Tải lên CSV</strong> ở trên để tiến hành kiểm tra và nạp dữ liệu.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Success Banner
        row_count = len(state.raw_df)
        col_count = len(state.raw_df.columns)

        st.markdown(
            f"""
            <div class="ci-banner">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="width: 42px; height: 42px; border-radius: 50%; background: rgba(0, 106, 97, 0.12); color: #006a61; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: bold;">
                        ✓
                    </div>
                    <div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #0b1c30;">Dataset đã sẵn sàng</div>
                        <div style="font-size: 0.85rem; color: #464555;">Dữ liệu đáp ứng đầy đủ yêu cầu cấu trúc của quy trình phân tích.</div>
                    </div>
                </div>
                <div style="display: flex; gap: 12px;">
                    <div class="ci-stat-box">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #0b1c30;">{row_count:,}</div>
                        <div style="font-size: 10px; font-weight: 600; color: #464555; text-transform: uppercase;">Khách hàng</div>
                    </div>
                    <div class="ci-stat-box">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #0b1c30;">{col_count}</div>
                        <div style="font-size: 10px; font-weight: 600; color: #464555; text-transform: uppercase;">Thuộc tính</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.code(f"SHA-256: {state.dataset_signature}", language=None)

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # Quality & Checklist
        render_quality_section(state.raw_df)

        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

        # Raw Data Preview
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin: 0;">
                    Xem trước dữ liệu
                </h3>
                <span style="font-size: 0.85rem; color: #464555;">Hiển thị 20 dòng đầu tiên của dữ liệu gốc</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(state.raw_df.head(20), width="stretch", hide_index=True)

        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

        # Bottom Next-Step Action
        col_space, col_action = st.columns([1, 1])
        with col_action:
            if st.button("Tiếp tục: Khám phá dữ liệu →", type="primary", use_container_width=True):
                st.switch_page("views/2_Kham_pha_du_lieu.py")
            st.caption("Bước tiếp theo: Khám phá phân phối và tiền xử lý RFM")


render_page()
