"""Shared layout and native navigation helpers for TV5."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from components.workflow import render_progress


NAV_ITEMS = [
    ("0_Tong_quan.py", "Tổng quan"),
    ("1_Du_lieu.py", "Dữ liệu"),
    ("2_Kham_pha_du_lieu.py", "Khám phá dữ liệu"),
    ("3_Chon_K.py", "Chọn K"),
    ("4_Phan_cum.py", "Phân cụm"),
    ("5_Ket_qua.py", "Kết quả"),
    ("6_Thuat_toan.py", "Thuật toán"),
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

    st.sidebar.title("CustomerInsight AI")
    render_progress(state)
