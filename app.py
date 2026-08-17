"""CustomerInsight AI Streamlit application shell."""

import streamlit as st

from components.layout import build_navigation, render_navigation_rail, render_top_bar
from components.states import get_app_state
from components.theme import apply_custom_theme
from components.workflow import consume_flash


st.set_page_config(
    page_title="CustomerInsight AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_custom_theme()

app_state = get_app_state()
flash = consume_flash(st.session_state)
if flash is not None:
    getattr(st, flash.level, st.info)(flash.text)

current_page = build_navigation()
render_navigation_rail(app_state, current_page=current_page)
render_top_bar()
if current_page is None:
    st.error("Không tìm thấy trang ứng dụng nào.")
else:
    current_page.run()
