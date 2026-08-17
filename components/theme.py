"""Shared theme and CSS tokens matching the Stitch design system."""

import streamlit as st

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary-color: #3525cd;
    --primary-hover: #281ba5;
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
    background-color: var(--background-color) !important;
}

/* Suppress Streamlit default toolbar, deploy button, decoration & native sidebar */
[data-testid="stToolbar"],
.stDeployButton,
#MainMenu,
footer,
[data-testid="stDecoration"],
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
    visibility: hidden !important;
}

header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
}

/* Fixed 280px Navigation Rail */
.st-key-ci_nav_rail {
    position: fixed !important;
    left: 0 !important;
    top: 0 !important;
    bottom: 0 !important;
    width: 280px !important;
    height: 100vh !important;
    background-color: #ffffff !important;
    border-right: 1px solid #dce9ff !important;
    box-shadow: 2px 0 16px rgba(53, 37, 205, 0.03) !important;
    z-index: 999 !important;
    padding: 1.25rem 1rem 1.5rem 1rem !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    overflow-y: auto !important;
}

/* Brand inside rail */
.ci-nav-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding: 4px 6px;
}

.ci-nav-logo {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: #3525cd;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 16px;
    box-shadow: 0 4px 12px rgba(53, 37, 205, 0.25);
    flex-shrink: 0;
}

.ci-nav-title {
    font-weight: 700;
    font-size: 15px;
    color: #0b1c30;
    line-height: 1.2;
}

.ci-nav-subtitle {
    font-size: 10px;
    color: #464555;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}

/* Links container inside rail */
.ci-nav-links {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-bottom: auto;
}

/* Keyed navigation item wrapper containers */
.st-key-ci_nav_rail div[class*="st-key-ci_nav_item_"] {
    width: 100% !important;
    border-radius: 8px !important;
    margin-bottom: 3px !important;
    transition: all 0.15s ease !important;
    box-sizing: border-box !important;
}

/* Inactive Nav Wrapper */
.st-key-ci_nav_rail div[class*="st-key-ci_nav_item_"][class*="_inactive"] {
    background-color: transparent !important;
    border-left: 4px solid transparent !important;
}

.st-key-ci_nav_rail div[class*="st-key-ci_nav_item_"][class*="_inactive"]:hover {
    background-color: #eff4ff !important;
}

.st-key-ci_nav_rail div[class*="st-key-ci_nav_item_"][class*="_inactive"] [data-testid="stPageLink-NavLink"] {
    color: #464555 !important;
    font-weight: 500 !important;
}

/* Active Nav Wrapper — Deterministic Pale Indigo + Left Accent */
.st-key-ci_nav_rail div[class*="st-key-ci_nav_item_"][class*="_active"] {
    background-color: #e5eeff !important;
    border-left: 4px solid #3525cd !important;
    border-top-left-radius: 4px !important;
    border-bottom-left-radius: 4px !important;
    border-top-right-radius: 8px !important;
    border-bottom-right-radius: 8px !important;
}

.st-key-ci_nav_rail div[class*="st-key-ci_nav_item_"][class*="_active"] [data-testid="stPageLink-NavLink"],
.st-key-ci_nav_rail div[class*="st-key-ci_nav_item_"][class*="_active"] [data-testid="stPageLink-NavLink"] * {
    color: #3525cd !important;
    font-weight: 700 !important;
}

/* Base stPageLink resetting inside rail containers */
.st-key-ci_nav_rail [data-testid="stPageLink"],
.st-key-ci_nav_rail [data-testid="stPageLink"] > a,
.st-key-ci_nav_rail [data-testid="stPageLink-NavLink"] {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    text-decoration: none !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

.st-key-ci_nav_rail [data-testid="stPageLink-NavLink"] {
    padding: 8px 12px !important;
    font-size: 0.88rem !important;
    border: none !important;
    border-radius: inherit !important;
}

/* Workflow section at bottom */
.ci-nav-workflow {
    margin-top: auto;
    padding-top: 16px;
    border-top: 1px solid #dce9ff;
}

.ci-nav-wf-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 0.82rem;
}

.ci-nav-wf-title {
    font-weight: 600;
    color: #0b1c30;
}

.ci-nav-wf-step {
    color: #464555;
    font-size: 0.78rem;
}

/* Single clean workflow progress track */
.ci-single-progress-track {
    width: 100%;
    height: 8px;
    background-color: #e5eeff;
    border-radius: 9999px;
    overflow: hidden;
    margin-top: 6px;
    margin-bottom: 4px;
}

.ci-single-progress-fill {
    height: 100%;
    background-color: #3525cd;
    border-radius: 9999px;
    transition: width 0.3s ease;
}

/* Hide native progress widget in rail so only the single HTML track is visible */
.st-key-ci_nav_rail [data-testid="stProgress"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

.ci-nav-complete {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #3525cd;
    font-size: 0.82rem;
    font-weight: 600;
    margin-top: 8px;
}

/* Main Content Container offset by 280px rail */
.block-container {
    max-width: 1440px !important;
    padding: 0 2.5rem 3rem 2.5rem !important;
    margin-left: 280px !important;
    margin-right: auto !important;
    width: calc(100% - 280px) !important;
}

/* Top Navigation / Breadcrumb Bar */
.ci-top-bar {
    position: sticky;
    top: 0;
    z-index: 99;
    background-color: rgba(248, 249, 255, 0.95);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid #dce9ff;
    padding: 14px 0;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.ci-breadcrumb {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
}

.ci-breadcrumb-root {
    color: #464555;
    font-weight: 500;
}

.ci-breadcrumb-sep {
    color: #767586;
    font-size: 14px;
}

.ci-breadcrumb-current {
    color: #0b1c30;
    font-weight: 600;
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

/* Before / After Cards */
.ci-before-after-card {
    background-color: var(--surface-container-lowest);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 2px 8px rgba(53, 37, 205, 0.03);
}

/* Pipeline Centerpiece */
.ci-pipeline-card {
    background-color: var(--surface-container-lowest);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

/* Cluster Profile Card */
.ci-profile-card {
    background-color: var(--surface-container-lowest);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(53, 37, 205, 0.03);
    transition: all 0.2s ease-in-out;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.ci-profile-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(53, 37, 205, 0.08);
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
