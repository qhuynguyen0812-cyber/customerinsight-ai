from __future__ import annotations

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from components.states import APP_STATE_KEY
from src.state import new_app_state


ROOT = Path(__file__).resolve().parents[1]


def download_buttons(app: AppTest):
    return app.get("download_button")


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


def _valid_profile() -> pd.DataFrame:
    return pd.DataFrame({
        "Cluster": [0], "SegmentName": ["Active"], "count": [1],
        "mean Recency": [2.0], "mean Frequency": [5.0], "mean Monetary": [90.0],
    })


def _valid_metadata() -> dict[str, object]:
    return {
        "k": 3, "init": "k-means++", "n_init": 10, "random_state": 42,
        "max_iter": 300, "tol": 0.0001, "inertia": 8.5,
        "silhouette": 0.61, "iterations": 7, "runtime_seconds": 0.04,
    }


def _valid_state():
    state = new_app_state()
    state.results = _valid_results()
    state.cluster_profiles = _valid_profile()
    state.run_metadata = _valid_metadata()
    return state


def test_results_page_is_safely_gated_without_current_results() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py")).run()
    assert not app.exception
    assert len(app.info) == 1
    assert len(download_buttons(app)) == 0
    assert len(app.dataframe) == 0


def test_results_page_renders_current_mapping_and_export() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py"))
    app.session_state[APP_STATE_KEY] = _valid_state()
    app.run()
    assert not app.exception
    assert len(app.dataframe) == 2
    assert len(app.json) == 1
    assert len(download_buttons(app)) == 1
    assert download_buttons(app)[0].label == "Tải CSV kết quả khách hàng"


def test_invalid_current_payload_shows_error_without_export() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py"))
    state = _valid_state()
    state.results = pd.DataFrame({"CustomerID": ["C-001"]})
    app.session_state[APP_STATE_KEY] = state
    app.run()
    assert not app.exception
    assert len(app.error) == 1
    assert len(download_buttons(app)) == 0


def test_results_page_warns_and_does_not_render_invalid_run_metadata() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py"))
    state = _valid_state()
    state.run_metadata = {"k": 4, "inertia": 8.5}
    app.session_state[APP_STATE_KEY] = state
    app.run()
    assert not app.exception
    assert len(app.error) == 1
    assert len(app.json) == 0
    assert len(download_buttons(app)) == 0


def test_stale_legacy_keys_do_not_override_canonical_app_state() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "5_Ket_qua.py"))
    app.session_state[APP_STATE_KEY] = _valid_state()
    app.session_state["results_valid"] = True
    app.session_state["customer_results"] = pd.DataFrame({"CustomerID": ["STALE"]})
    app.run()
    assert not app.exception
    assert len(download_buttons(app)) == 1
    assert app.dataframe[0].value["CustomerID"].tolist() == ["C-001"]


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
