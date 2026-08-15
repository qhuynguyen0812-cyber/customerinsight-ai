"""Results page: a read-only consumer of current TV4/TV5 outputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from components.results_export import (
    ResultContractError,
    available_run_metadata,
    customer_results_to_csv_bytes,
    validate_customer_results,
    validate_profile,
)


# TV5 owns these state values. TV6 documents this consumer seam and never
# mutates them. The validity flag must only be true for the active signatures.
RESULTS_VALID_KEY = "results_valid"
CUSTOMER_RESULTS_KEY = "customer_results"
CLUSTER_PROFILES_KEY = "cluster_profiles"
RUN_METADATA_KEY = "run_metadata"


def render_results_page(state: Mapping[str, Any]) -> None:
    """Render only outputs declared current by the upstream state owner."""
    st.title("Kết quả phân cụm")
    if state.get(RESULTS_VALID_KEY) is not True:
        st.info("Chưa có kết quả hợp lệ. Hãy hoàn tất bước Phân cụm trước khi xem hoặc xuất dữ liệu.")
        return

    try:
        customers = validate_customer_results(state.get(CUSTOMER_RESULTS_KEY))
    except ResultContractError as error:
        st.error(f"Không thể hiển thị kết quả hiện tại: {error}")
        return

    st.subheader("Khám phá khách hàng")
    query = st.text_input("Tìm CustomerID", key="tv6_customer_query")
    visible = customers
    if query.strip():
        visible = customers[
            customers["CustomerID"].astype(str).str.contains(query.strip(), case=False, regex=False)
        ]
    st.dataframe(visible, width="stretch", hide_index=True)

    profile = state.get(CLUSTER_PROFILES_KEY)
    if profile is not None:
        try:
            st.subheader("Hồ sơ cụm")
            st.dataframe(validate_profile(profile), width="stretch", hide_index=True)
        except ResultContractError as error:
            st.warning(f"Hồ sơ cụm chưa sẵn sàng: {error}")

    metadata = state.get(RUN_METADATA_KEY)
    if metadata is not None:
        try:
            current_metadata = available_run_metadata(metadata)
            st.subheader("Thông tin lần chạy")
            st.json(current_metadata)
        except ResultContractError as error:
            st.warning(f"Thông tin lần chạy chưa sẵn sàng: {error}")

    st.download_button(
        "Tải CSV kết quả khách hàng",
        data=customer_results_to_csv_bytes(customers),
        file_name="customer_results.csv",
        mime="text/csv",
        key="tv6_customer_export",
    )


render_results_page(st.session_state)
