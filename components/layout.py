"""Shared layout/navigation helpers for TV5."""
from __future__ import annotations

from pathlib import Path

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


def build_navigation():
    """Use Streamlit's native navigation when page files exist."""
    pages = []
    views_dir = Path(__file__).resolve().parents[1] / "views"
    for filename, title in NAV_ITEMS:
        page = views_dir / filename
        if page.exists():
            pages.append(st.Page(str(page), title=title, icon="📄"))
    if pages:
        return st.navigation(pages)
    return None


def render_sidebar() -> None:
    st.sidebar.title("CustomerInsight AI")
    render_progress()
