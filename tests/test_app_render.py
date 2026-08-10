from __future__ import annotations

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def _valid_results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerID": ["C-001"],
            "Recency": [2.0],
            "Frequency": [5.0],
            "Monetary": [90.0],
            "Cluster": [0],
            "SegmentName": ["Active"],
        }
    )


def test_results_page_is_safely_gated_without_current_results() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py")).run()
    assert not app.exception
    assert len(app.info) == 1
    assert len(app.download_button) == 0
    assert len(app.dataframe) == 0


def test_results_page_renders_current_mapping_and_export() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py"))
    app.session_state["results_valid"] = True
    app.session_state["customer_results"] = _valid_results()
    app.run()
    assert not app.exception
    assert len(app.dataframe) == 1
    assert len(app.download_button) == 1
    assert app.download_button[0].label == "Tải CSV kết quả khách hàng"


def test_invalid_current_payload_shows_error_without_export() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py"))
    app.session_state["results_valid"] = True
    app.session_state["customer_results"] = pd.DataFrame({"CustomerID": ["C-001"]})
    app.run()
    assert not app.exception
    assert len(app.error) == 1
    assert len(app.download_button) == 0


def test_results_page_warns_and_does_not_render_invalid_run_metadata() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py"))
    app.session_state["results_valid"] = True
    app.session_state["customer_results"] = _valid_results()
    app.session_state["run_metadata"] = {"k": 4, "inertia": 8.5}
    app.run()
    assert not app.exception
    assert len(app.warning) == 1
    assert "Thông tin lần chạy chưa sẵn sàng" in app.warning[0].value
    assert len(app.json) == 0


def test_algorithm_page_renders_academic_content_and_visual() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "6_Thuat_toan.py")).run()
    assert not app.exception
    rendered = " ".join(
        element.value
        for group in (app.title, app.header, app.subheader, app.markdown, app.info)
        for element in group
    )
    for term in ("Centroid", "Inertia", "Silhouette", "Lloyd", "K-Means++", "Điểm mạnh", "Hạn chế"):
        assert term in rendered
    assert len(app.slider) == 1
    assert len(app.get("plotly_chart")) == 1


def test_algorithm_interaction_does_not_create_production_result_state() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "6_Thuat_toan.py")).run()
    app.slider[0].set_value(4).run()
    assert not app.exception
    for key in ("results_valid", "customer_results", "cluster_profiles", "run_metadata"):
        assert key not in app.session_state
