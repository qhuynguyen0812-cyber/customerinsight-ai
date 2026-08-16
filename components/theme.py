"""Shared theme and CSS tokens matching the Stitch design system."""

import streamlit as st

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --primary-color: #3525cd;
    --cluster-01: #3525cd;
    --cluster-02: #006a61;
    --cluster-03: #8b5cf6;
    --background-color: #f8f9ff;
    --surface-container-lowest: #ffffff;
    --surface-container-low: #eff4ff;
    --surface-container: #e5eeff;
    --surface-container-high: #dce9ff;
    --on-surface: #0b1c30;
    --on-surface-variant: #464555;
    --outline-variant: #dce9ff;
    --border-color: #e2dfff;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: var(--on-surface);
}

.stApp {
    background-color: var(--background-color);
}

/* Custom Card Container */
.ci-card {
    background-color: var(--surface-container-lowest);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 16px rgba(53, 37, 205, 0.04);
    transition: all 0.2s ease-in-out;
}

.ci-card:hover {
    box-shadow: 0 8px 24px rgba(53, 37, 205, 0.08);
    border-color: #c3c0ff;
}

/* Badge Pill */
.ci-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 9999px;
    background-color: rgba(53, 37, 205, 0.08);
    border: 1px solid rgba(53, 37, 205, 0.2);
    color: #3525cd;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* Feature Chip */
.ci-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 9999px;
    background-color: #eff4ff;
    color: var(--on-surface-variant);
    font-size: 12px;
    font-weight: 500;
}

.ci-chip-dot-teal {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #006a61;
}

.ci-chip-dot-indigo {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #3525cd;
}

.ci-chip-dot-violet {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #8b5cf6;
}

/* Journey Step Cards */
.ci-step-card {
    background-color: var(--surface-container-lowest);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    height: 100%;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.ci-step-number {
    position: absolute;
    right: 12px;
    top: 6px;
    font-size: 54px;
    font-weight: 800;
    color: rgba(53, 37, 205, 0.06);
    line-height: 1;
    user-select: none;
}

.ci-step-badge {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: #3525cd;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 12px;
}

/* Status Banner */
.ci-banner {
    background-color: var(--surface-container-low);
    border: 1px solid var(--outline-variant);
    border-radius: 16px;
    padding: 20px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}

/* Stat Box */
.ci-stat-box {
    background-color: #ffffff;
    border: 1px solid var(--outline-variant);
    border-radius: 12px;
    padding: 10px 18px;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

/* Assessment Box */
.ci-assessment-box {
    background: linear-gradient(135deg, rgba(53, 37, 205, 0.04) 0%, rgba(139, 92, 246, 0.04) 100%);
    border: 1px solid rgba(53, 37, 205, 0.18);
    border-radius: 12px;
    padding: 18px 20px;
}

/* Streamlit button custom styles */
.stButton > button[kind="primary"] {
    background-color: #3525cd !important;
    border-color: #3525cd !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.25rem !important;
    transition: all 0.15s ease !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #281ba5 !important;
    border-color: #281ba5 !important;
    box-shadow: 0 4px 12px rgba(53, 37, 205, 0.25) !important;
}

.stButton > button[kind="secondary"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    border-color: var(--border-color) !important;
}
</style>
"""


def apply_custom_theme() -> None:
    """Inject custom CSS matching the Stitch design system."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
