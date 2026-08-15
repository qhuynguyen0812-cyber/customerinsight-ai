"""CustomerInsight AI Streamlit shell.

Bootstrap only. Feature implementation belongs to the assigned TV branches.
"""

import streamlit as st

from components.states import get_app_state
from components.workflow import consume_flash, progress_fraction, workflow_stage


st.set_page_config(page_title="CustomerInsight AI", page_icon="📊", layout="wide")

st.title("CustomerInsight AI")
st.caption("Customer Segmentation using K-Means")

# The shell is intentionally thin: individual feature pages own their business
# logic, while TV5 supplies a single state/progress/feedback contract to all of
# them.  Calling this once is enough to initialise a durable per-user session.
app_state = get_app_state()
flash = consume_flash(st.session_state)
if flash is not None:
    getattr(st, flash.level, st.info)(flash.text)

stage = workflow_stage(app_state)
st.sidebar.progress(progress_fraction(app_state), text=f"Workflow: {stage}/5")

st.info(
    "Team baseline is ready. Functional pages and ML behavior are implemented "
    "on the assigned feature branches according to the locked specification package."
)
