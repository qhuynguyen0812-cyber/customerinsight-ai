"""Release-level HTTP evidence for TV6 freshness and isolation contracts."""

from __future__ import annotations

import codecs
from io import BytesIO

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from components.results_export import CUSTOMER_RESULT_COLUMNS
from web.app import app


def _full_run(client: TestClient, *, k: int = 3, strategy: str = "iqr_clip") -> dict:
    assert client.post("/api/dataset/sample").status_code == 200
    assert client.post("/api/preprocess", json={"outlier_strategy": strategy}).status_code == 200
    assert client.post("/api/k-analysis", json={"k_min": 2, "k_max": 10}).status_code == 200
    assert client.post("/api/select-k", json={"selected_k": k}).status_code == 200
    clustered = client.post("/api/cluster")
    assert clustered.status_code == 200, clustered.text
    results = client.get("/api/results")
    assert results.status_code == 200
    assert client.get("/api/export").status_code == 200
    return results.json()


def _read_export(payload: bytes) -> pd.DataFrame:
    return pd.read_csv(BytesIO(payload), encoding="utf-8-sig", dtype={"CustomerID": str})


def _assert_canonical_export(payload: bytes, *, k: int) -> pd.DataFrame:
    assert payload.startswith(codecs.BOM_UTF8)
    assert b"\r\n" not in payload
    exported = _read_export(payload)
    raw = pd.read_csv("data/sample_customers.csv", dtype={"CustomerID": str})
    assert list(exported.columns) == CUSTOMER_RESULT_COLUMNS
    assert len(exported) == len(raw) == 720
    assert exported["CustomerID"].is_unique
    assert set(exported["CustomerID"]) == set(raw["CustomerID"])
    pd.testing.assert_frame_equal(
        exported.loc[:, ["CustomerID", "Recency", "Frequency", "Monetary"]],
        raw.loc[:, ["CustomerID", "Recency", "Frequency", "Monetary"]],
        check_dtype=False,
    )
    assert exported["Cluster"].nunique() == k
    assert exported["SegmentName"].notna().all()
    return exported


def _assert_outputs_blocked(client: TestClient) -> None:
    state = client.get("/api/state").json()
    assert state["results_ready"] is False
    assert state["clustering_data"] is None
    assert client.get("/api/results").status_code == 422
    assert client.get("/api/export").status_code == 422
    assert client.get("/results", follow_redirects=False).status_code == 303


def test_new_dataset_invalidates_old_results_and_export() -> None:
    with TestClient(app) as client:
        old = _full_run(client)
        replacement = (
            "CustomerID,Recency,Frequency,Monetary\n"
            "NEW-1,10,2,50\nNEW-2,20,3,75\nNEW-3,30,4,100\n"
        )
        response = client.post(
            "/api/dataset/upload",
            files={"file": ("replacement.csv", replacement, "text/csv")},
        )
        assert response.status_code == 200
        assert response.json()["dataset_signature"] != old.get("dataset_signature")
        assert response.json()["preprocessed"] is False
        assert response.json()["k_analyzed"] is False
        assert response.json()["selected_k"] is None
        _assert_outputs_blocked(client)


def test_preprocessing_k_analysis_and_selected_k_changes_block_stale_outputs() -> None:
    with TestClient(app) as client:
        _full_run(client)

        assert client.post("/api/preprocess").status_code == 200
        state = client.get("/api/state").json()
        assert state["preprocessed"] is True
        assert state["k_analyzed"] is False
        assert state["selected_k"] is None
        _assert_outputs_blocked(client)

        assert client.post("/api/k-analysis", json={"k_min": 2, "k_max": 6}).status_code == 200
        assert client.post("/api/select-k", json={"selected_k": 3}).status_code == 200
        assert client.post("/api/cluster").status_code == 200

        assert client.post("/api/k-analysis", json={"k_min": 2, "k_max": 5}).status_code == 200
        assert client.get("/api/state").json()["selected_k"] is None
        _assert_outputs_blocked(client)

        assert client.post("/api/select-k", json={"selected_k": 3}).status_code == 200
        assert client.post("/api/cluster").status_code == 200
        assert client.post("/api/select-k", json={"selected_k": 5}).status_code == 200
        _assert_outputs_blocked(client)


def test_failed_upload_is_atomic_and_preserves_current_run() -> None:
    with TestClient(app) as client:
        before = _full_run(client)
        before_export = client.get("/api/export").content
        invalid = "CustomerID,Recency,Frequency\nBROKEN,1,2\n"
        response = client.post(
            "/api/dataset/upload",
            files={"file": ("invalid.csv", invalid, "text/csv")},
        )
        assert response.status_code == 422
        assert client.get("/api/results").json() == before
        assert client.get("/api/export").content == before_export


@pytest.mark.parametrize(
    "csv_text",
    [
        "not,a,valid,customer,file\n1,2,3,4,5\n",
        "CustomerID,Recency,Frequency,Monetary\nC1,1,2,3\nC1,2,3,4\n",
        "CustomerID,Recency,Frequency,Monetary\nC1,text,2,3\n",
        "CustomerID,Recency,Frequency,Monetary\nC1,-1,2,3\n",
        "CustomerID,Recency,Frequency,Monetary\nC1,1,2,inf\n",
    ],
)
def test_invalid_upload_variants_never_partially_replace_a_valid_run(csv_text: str) -> None:
    with TestClient(app) as client:
        before = _full_run(client)
        before_export = client.get("/api/export").content
        response = client.post(
            "/api/dataset/upload",
            files={"file": ("invalid.csv", csv_text, "text/csv")},
        )
        assert response.status_code == 422
        assert client.get("/api/results").json() == before
        assert client.get("/api/export").content == before_export


def test_invalid_k_requests_are_atomic_and_do_not_expose_partial_state() -> None:
    with TestClient(app) as client:
        before = _full_run(client)
        before_export = client.get("/api/export").content

        invalid_range = client.post("/api/k-analysis", json={"k_min": 8, "k_max": 2})
        assert invalid_range.status_code == 422
        assert client.get("/api/results").json() == before
        assert client.get("/api/export").content == before_export

        invalid_selection = client.post("/api/select-k", json={"selected_k": 99})
        assert invalid_selection.status_code == 422
        assert client.get("/api/results").json() == before
        assert client.get("/api/export").content == before_export


def test_missing_rfm_upload_is_valid_json_and_can_be_preprocessed() -> None:
    with TestClient(app) as client:
        missing = (
            "CustomerID,Recency,Frequency,Monetary\n"
            "C1,,5,100\nC2,20,,50\nC3,30,8,\n"
        )
        response = client.post(
            "/api/dataset/upload",
            files={"file": ("missing.csv", missing, "text/csv")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["eda_data"]["missing_count"] == 3
        assert payload["preview"][0]["Recency"] is None
        assert payload["preview"][1]["Frequency"] is None
        assert payload["preview"][2]["Monetary"] is None
        processed = client.post("/api/preprocess")
        assert processed.status_code == 200, processed.text
        assert processed.json()["eda_data"]["missing_count"] == 3
        chart_data = processed.json()["eda_data"]["chart_data"]
        assert all(value is None or isinstance(value, (int, float)) for values in chart_data.values() for value in values["raw"])


def test_sessions_are_isolated_in_both_directions() -> None:
    with TestClient(app) as client_a, TestClient(app) as client_b:
        _full_run(client_a)
        assert client_b.get("/api/state").json()["dataset_loaded"] is False
        assert client_b.get("/api/results").status_code == 422
        assert client_b.get("/api/export").status_code == 422

        replacement = (
            "CustomerID,Recency,Frequency,Monetary\n"
            "B1,1,2,3\nB2,4,5,6\nB3,7,8,9\n"
        )
        assert client_b.post(
            "/api/dataset/upload",
            files={"file": ("b.csv", replacement, "text/csv")},
        ).status_code == 200
        assert client_a.get("/api/results").status_code == 200
        assert client_a.get("/api/export").status_code == 200


def test_dynamic_k5_export_is_current_complete_and_deterministic() -> None:
    with TestClient(app) as client:
        results = _full_run(client, k=5)
        assert results["selected_k"] == 5
        assert results["run_metadata"]["k"] == 5
        assert len(results["cluster_profiles"]) == 5
        assert sum(profile["count"] for profile in results["cluster_profiles"]) == 720

        first = client.get("/api/export").content
        second = client.get("/api/export").content
        assert first == second
        assert first.startswith(codecs.BOM_UTF8)
        assert b"\r\n" not in first
        exported = pd.read_csv(BytesIO(first), encoding="utf-8-sig", dtype={"CustomerID": str})
        raw = pd.read_csv("data/sample_customers.csv", dtype={"CustomerID": str})
        assert list(exported.columns) == CUSTOMER_RESULT_COLUMNS
        assert exported["CustomerID"].is_unique
        assert set(exported["CustomerID"]) == set(raw["CustomerID"])
        pd.testing.assert_frame_equal(
            exported.loc[:, ["CustomerID", "Recency", "Frequency", "Monetary"]],
            raw.loc[:, ["CustomerID", "Recency", "Frequency", "Monetary"]],
            check_dtype=False,
        )
        assert exported["Cluster"].nunique() == 5
        assert exported["SegmentName"].notna().all()


@pytest.mark.parametrize(
    ("strategy", "inertia", "silhouette", "iterations"),
    [
        ("iqr_clip", 611.4205381920901, 0.45877917738169266, 9),
        ("keep", 882.5145827792722, 0.4502395249927606, 11),
    ],
)
def test_canonical_phase2_workflows_publish_current_results_and_export(
    strategy: str, inertia: float, silhouette: float, iterations: int
) -> None:
    with TestClient(app) as client:
        results = _full_run(client, strategy=strategy)
        state = client.get("/api/state").json()
        assert state["row_count"] == results["row_count"] == 720
        assert state["outlier_strategy"] == strategy
        assert state["eda_data"]["iqr_applied"] is (strategy == "iqr_clip")
        if strategy == "keep":
            assert state["eda_data"]["before_after"]["Monetary"]["pct_clipped"] == 0.0
        assert results["selected_k"] == 3
        assert results["run_metadata"]["inertia"] == pytest.approx(inertia, abs=0.0001)
        assert results["run_metadata"]["silhouette"] == pytest.approx(silhouette, abs=0.0001)
        assert results["run_metadata"]["iterations"] == iterations
        assert len(results["cluster_profiles"]) == 3
        assert sum(profile["count"] for profile in results["cluster_profiles"]) == 720
        first = client.get("/api/export").content
        assert client.get("/api/export").content == first
        _assert_canonical_export(first, k=3)


def test_solver_override_invalidates_only_fit_outputs_then_reaches_model_metadata() -> None:
    with TestClient(app) as client:
        _full_run(client)
        before = client.get("/api/state").json()
        response = client.post("/api/solver-preferences", json={"max_iter": 400, "tol": 0.0002})
        assert response.status_code == 200
        changed = response.json()
        assert changed["solver_preferences"] == {"max_iter": 400, "tol": 0.0002}
        for field in ("dataset_signature", "preprocessing_signature", "selected_k"):
            assert changed[field] == before[field]
        assert changed["preprocessed"] is True
        assert changed["k_analyzed"] is True
        assert changed["k_analysis_data"]["recommended_k"] == before["k_analysis_data"]["recommended_k"]
        _assert_outputs_blocked(client)

        assert client.post("/api/cluster").status_code == 200
        results = client.get("/api/results").json()
        metadata = results["run_metadata"]
        assert metadata["k"] == results["selected_k"] == 3
        assert metadata["init"] == "k-means++"
        assert metadata["n_init"] == 10
        assert metadata["random_state"] == 42
        assert metadata["max_iter"] == 400
        assert metadata["tol"] == pytest.approx(0.0002)
        assert metadata["inertia"] > 0 and metadata["silhouette"] > 0
        assert metadata["iterations"] >= 1
        assert metadata["runtime_seconds"] is not None
        assert client.get("/api/export").status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        '{"max_iter":true}', '{"max_iter":3.5}', '{"max_iter":0}', '{"max_iter":-1}',
        '{"tol":true}', '{"tol":0}', '{"tol":-0.1}', '{"tol":NaN}',
        '{"tol":Infinity}', '{"tol":-Infinity}', '{"foo":1}',
    ],
)
def test_invalid_solver_configuration_is_release_atomic(payload: str) -> None:
    with TestClient(app) as client:
        before_results = _full_run(client)
        before_state = client.get("/api/state").json()
        before_export = client.get("/api/export").content
        response = client.post(
            "/api/solver-preferences", content=payload, headers={"content-type": "application/json"}
        )
        assert response.status_code == 422
        after_state = client.get("/api/state").json()
        assert after_state["solver_preferences"] == before_state["solver_preferences"]
        assert after_state["selected_k"] == before_state["selected_k"]
        assert client.get("/api/results").json() == before_results
        assert client.get("/api/export").content == before_export


@pytest.mark.parametrize("payload", ['{"outlier_strategy":"winsorize"}', '{broken'])
def test_invalid_outlier_configuration_is_release_atomic(payload: str) -> None:
    with TestClient(app) as client:
        before_results = _full_run(client)
        before_state = client.get("/api/state").json()
        before_export = client.get("/api/export").content
        response = client.post(
            "/api/preprocess", content=payload, headers={"content-type": "application/json"}
        )
        assert response.status_code == 422
        after_state = client.get("/api/state").json()
        for field in ("outlier_strategy", "preprocessing_signature", "selected_k"):
            assert after_state[field] == before_state[field]
        assert client.get("/api/results").json() == before_results
        assert client.get("/api/export").content == before_export


def test_strategy_change_preserves_inputs_and_invalidates_all_preprocessing_descendants() -> None:
    with TestClient(app) as client:
        _full_run(client)
        before = client.get("/api/state").json()
        response = client.post("/api/preprocess", json={"outlier_strategy": "keep"})
        assert response.status_code == 200
        changed = response.json()
        assert changed["dataset_loaded"] is True
        assert changed["dataset_signature"] == before["dataset_signature"]
        assert changed["solver_preferences"] == before["solver_preferences"]
        assert changed["preprocessed"] is True
        assert changed["outlier_strategy"] == "keep"
        assert changed["k_analyzed"] is False
        assert changed["k_analysis_data"] is None
        assert changed["selected_k"] is None
        _assert_outputs_blocked(client)

        assert client.post("/api/k-analysis", json={"k_min": 2, "k_max": 10}).status_code == 200
        assert client.post("/api/select-k", json={"selected_k": 3}).status_code == 200
        assert client.post("/api/cluster").status_code == 200
        assert client.get("/api/results").status_code == 200
        assert client.get("/api/export").status_code == 200


def test_phase2_configuration_and_outputs_are_session_isolated() -> None:
    with TestClient(app) as client_a, TestClient(app) as client_b:
        _full_run(client_a, strategy="keep")
        assert client_a.post(
            "/api/solver-preferences", json={"max_iter": 400, "tol": 0.0002}
        ).status_code == 200
        assert client_a.post("/api/cluster").status_code == 200
        a_before = client_a.get("/api/state").json()
        assert a_before["outlier_strategy"] == "keep"

        b_fresh = client_b.get("/api/state").json()
        assert b_fresh["dataset_loaded"] is False
        assert b_fresh["outlier_strategy"] == "iqr_clip"
        assert b_fresh["solver_preferences"] == {"max_iter": 300, "tol": 0.0001}
        assert b_fresh["selected_k"] is None
        _full_run(client_b)

        a_after = client_a.get("/api/state").json()
        assert a_after["dataset_signature"] == a_before["dataset_signature"]
        assert a_after["outlier_strategy"] == "keep"
        assert a_after["solver_preferences"] == {"max_iter": 400, "tol": 0.0002}
        assert a_after["selected_k"] == 3
        assert client_a.get("/api/results").status_code == 200
        assert client_a.get("/api/export").status_code == 200
