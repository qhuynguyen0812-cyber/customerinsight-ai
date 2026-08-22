"""Release-level HTTP evidence for TV6 freshness and isolation contracts."""

from __future__ import annotations

import codecs
from io import BytesIO

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from components.results_export import CUSTOMER_RESULT_COLUMNS
from web.app import app


def _full_run(client: TestClient, *, k: int = 3) -> dict:
    assert client.post("/api/dataset/sample").status_code == 200
    assert client.post("/api/preprocess").status_code == 200
    assert client.post("/api/k-analysis", json={"k_min": 2, "k_max": 10}).status_code == 200
    assert client.post("/api/select-k", json={"selected_k": k}).status_code == 200
    clustered = client.post("/api/cluster")
    assert clustered.status_code == 200, clustered.text
    results = client.get("/api/results")
    assert results.status_code == 200
    assert client.get("/api/export").status_code == 200
    return results.json()


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
