"""Shared layout and native navigation helpers for TV5."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from components.theme import apply_custom_theme
from components.workflow import render_progress


NAV_ITEMS = [
    ("0_Tong_quan.py", "Tổng quan"),
    ("1_Du_lieu.py", "Dữ liệu"),
    ("2_Kham_pha_du_lieu.py", "Khám phá dữ liệu"),
    ("3_Chon_K.py", "Chọn K"),
    ("4_Phan_cum.py", "Phân cụm"),
    ("5_Ket_qua.py", "Kết quả"),
]


def build_navigation() -> Any | None:
    """Build the application's single native multipage navigation object."""

    views_dir = Path(__file__).resolve().parents[1] / "views"
    pages = [
        st.Page(str(views_dir / filename), title=title, icon="📄")
        for filename, title in NAV_ITEMS
        if (views_dir / filename).is_file()
    ]
    return st.navigation(pages) if pages else None


def render_sidebar(state=None) -> None:
    """Render branding and canonical progress without creating another navigator."""

    apply_custom_theme()
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <div style="width: 36px; height: 36px; border-radius: 8px; background: #3525cd; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 15px;">CI</div>
            <div>
                <div style="font-weight: 700; font-size: 15px; color: #3525cd; line-height: 1.2;">CustomerInsight AI</div>
                <div style="font-size: 10px; color: #464555; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 500;">Enterprise Analytics</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_progress(state)

