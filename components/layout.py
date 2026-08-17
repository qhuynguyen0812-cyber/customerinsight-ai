"""Shared layout and native navigation helpers for TV5."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from components.theme import apply_custom_theme
from components.workflow import WorkflowStage, progress_fraction, workflow_stage


NAV_ITEMS = [
    ("0_Tong_quan.py", "Tổng quan"),
    ("1_Du_lieu.py", "Dữ liệu"),
    ("2_Kham_pha_du_lieu.py", "Khám phá dữ liệu"),
    ("3_Chon_K.py", "Chọn K"),
    ("4_Phan_cum.py", "Phân cụm"),
    ("5_Ket_qua.py", "Kết quả"),
]

PAGE_ICONS = {
    "0_Tong_quan.py": ":material/dashboard:",
    "1_Du_lieu.py": ":material/database:",
    "2_Kham_pha_du_lieu.py": ":material/explore:",
    "3_Chon_K.py": ":material/tune:",
    "4_Phan_cum.py": ":material/hub:",
    "5_Ket_qua.py": ":material/assessment:",
}


def build_navigation() -> Any | None:
    """Build the application's single native multipage navigation object as hidden router."""
    views_dir = Path(__file__).resolve().parents[1] / "views"
    pages = [
        st.Page(
            str(views_dir / filename),
            title=title,
            icon=PAGE_ICONS.get(filename),
        )
        for filename, title in NAV_ITEMS
        if (views_dir / filename).is_file()
    ]
    return st.navigation(pages, position="hidden") if pages else None


def render_top_bar() -> None:
    """Render the shared global top bar with breadcrumb."""
    top_bar_html = (
        '<div class="ci-top-bar">'
        '<div class="ci-breadcrumb">'
        '<span class="ci-breadcrumb-root">Dự án</span>'
        '<span class="ci-breadcrumb-sep">›</span>'
        '<span class="ci-breadcrumb-current">Customer Segmentation</span>'
        '</div>'
        '</div>'
    )
    st.markdown(top_bar_html, unsafe_allow_html=True)


def render_navigation_rail(state=None, current_page: Any | None = None) -> None:
    """Render deterministic 280px fixed navigation rail with Python-derived active wrappers."""
    apply_custom_theme()

    if state is None:
        from components.states import get_app_state
        state = get_app_state()

    stage = workflow_stage(state)
    frac = progress_fraction(state)
    pct = int(round(frac * 100))
    views_dir = Path(__file__).resolve().parents[1] / "views"

    completed_badge = ""
    if stage == WorkflowStage.RESULTS_READY:
        completed_badge = (
            '<div class="ci-nav-complete">'
            '<span>✓</span> <span>Phân tích hoàn tất</span>'
            '</div>'
        )

    with st.container(key="ci_nav_rail"):
        # 1. BRAND — TOP
        brand_html = (
            '<div class="ci-nav-brand">'
            '<div class="ci-nav-logo">CI</div>'
            '<div>'
            '<div class="ci-nav-title">CustomerInsight AI</div>'
            '<div class="ci-nav-subtitle">Enterprise Analytics</div>'
            '</div>'
            '</div>'
        )
        st.markdown(brand_html, unsafe_allow_html=True)

        # 2. NAVIGATION — MIDDLE (Keyed Active/Inactive Containers)
        for index, (filename, title) in enumerate(NAV_ITEMS):
            page_path = str(views_dir / filename)
            icon = PAGE_ICONS.get(filename)
            is_active = current_page is not None and getattr(current_page, "title", None) == title
            key = f"ci_nav_item_{index}_active" if is_active else f"ci_nav_item_{index}_inactive"
            with st.container(key=key):
                st.page_link(page_path, label=title, icon=icon, width="stretch")

        # 3. WORKFLOW — BOTTOM (Single HTML Progress Track + st.progress for test contract)
        workflow_html = (
            '<div class="ci-nav-workflow">'
            '<div class="ci-nav-wf-header">'
            '<span class="ci-nav-wf-title">Tiến độ phân tích</span>'
            f'<span class="ci-nav-wf-step">{int(stage)} / 5 bước hoàn tất</span>'
            '</div>'
            '<div class="ci-single-progress-track">'
            f'<div class="ci-single-progress-fill" style="width: {pct}%;"></div>'
            '</div>'
            f'{completed_badge}'
            '</div>'
        )
        st.markdown(workflow_html, unsafe_allow_html=True)
        st.progress(frac)


def render_sidebar(state=None, current_page: Any | None = None) -> None:
    """Alias for render_navigation_rail to maintain backward compatibility."""
    render_navigation_rail(state, current_page=current_page)
