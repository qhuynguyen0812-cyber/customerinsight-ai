"""CustomerInsight AI Streamlit application shell."""

import streamlit as st

from components.layout import build_navigation, render_sidebar
from components.states import get_app_state
from components.workflow import consume_flash


st.set_page_config(page_title="CustomerInsight AI", page_icon="📊", layout="wide")

app_state = get_app_state()
flash = consume_flash(st.session_state)
if flash is not None:
    getattr(st, flash.level, st.info)(flash.text)

render_sidebar(app_state)
navigation = build_navigation()
if navigation is None:
    st.error("Không tìm thấy trang ứng dụng nào.")
else:
    navigation.run()
