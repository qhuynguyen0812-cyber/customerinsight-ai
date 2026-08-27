"""FastAPI Web Endpoints and Workflow Integration Tests."""

import asyncio
import io
import json
import math
from pathlib import Path
import re
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.datastructures import UploadFile

from web.app import (
    app,
    overview,
    data_page,
    eda_page,
    choose_k_page,
    clustering_page,
    results_page,
    get_state,
    load_sample,
    upload_dataset,
    preprocess_dataset,
    run_k_analysis,
    select_k,
    run_cluster,
    get_results_data,
    export_results_csv,
    save_solver_preferences,
)


def make_request(method: str, path: str, session_id: str = "test-session-web", body_bytes: bytes = b"") -> Request:
    headers = [
        (b"host", b"testserver"),
        (b"cookie", f"customerinsight_session={session_id}".encode("latin1")),
    ]
    if body_bytes:
        headers.append((b"content-type", b"application/json"))
        headers.append((b"content-length", str(len(body_bytes)).encode("ascii")))

    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers,
        "query_string": b"",
    }
    return Request(scope, receive)


def test_overview_page():
    req = make_request("GET", "/", "sess-overview")
    resp = overview(req)
    assert resp.status_code == 200


def test_fresh_session_state_and_data_page():
    sid = "sess-fresh"
    req_page = make_request("GET", "/data", sid)
    resp_page = data_page(req_page)
    assert resp_page.status_code == 200

    req_state = make_request("GET", "/api/state", sid)
    resp_state = get_state(req_state)
    assert resp_state.status_code == 200
    state = json.loads(resp_state.body)
    assert state["dataset_loaded"] is False
    assert state["preprocessed"] is False
    assert state["workflow_progress"]["completed_steps"] == 0
    assert state["workflow_progress"]["percent"] == 0


def test_load_sample_dataset():
    sid = "sess-sample"
    req = make_request("POST", "/api/dataset/sample", sid)
    resp = load_sample(req)
    assert resp.status_code == 200
    state = json.loads(resp.body)
    assert state["dataset_loaded"] is True
    assert state["row_count"] == 720
    assert state["dataset_signature"] == "622a6cff9d8b41106268eb1e31e50b5259ccc1d4c318a15a5c496c8edce2a96f"
    assert sum(state["quality_report"]["iqr_outlier_by_column"].values()) == 117
    assert state["workflow_progress"]["completed_steps"] == 1
    assert state["workflow_progress"]["percent"] == 20


def test_upload_csv_valid_and_invalid():
    async def _run():
        sid = "sess-upload"

        # 1. Valid CSV
        valid_csv = "CustomerID,Recency,Frequency,Monetary\nC1,10,5,100\nC2,20,2,50\nC3,30,8,200\n"
        f1 = UploadFile(filename="valid.csv", file=io.BytesIO(valid_csv.encode("utf-8")))
        r1 = await upload_dataset(make_request("POST", "/api/dataset/upload", sid), f1)
        assert r1.status_code == 200
        st1 = json.loads(r1.body)
        assert st1["dataset_loaded"] is True
        assert st1["row_count"] == 3

        # 2. Missing required column
        missing_csv = "CustomerID,Recency,Frequency\nC1,10,5\n"
        f2 = UploadFile(filename="missing.csv", file=io.BytesIO(missing_csv.encode("utf-8")))
        r2 = await upload_dataset(make_request("POST", "/api/dataset/upload", sid), f2)
        assert r2.status_code == 422
        assert "detail" in json.loads(r2.body)

        # 3. Invalid non-numeric data
        invalid_csv = "CustomerID,Recency,Frequency,Monetary\nC1,abc,5,100\n"
        f3 = UploadFile(filename="invalid.csv", file=io.BytesIO(invalid_csv.encode("utf-8")))
        r3 = await upload_dataset(make_request("POST", "/api/dataset/upload", sid), f3)
        assert r3.status_code == 422
        assert "detail" in json.loads(r3.body)

    asyncio.run(_run())


def test_gating_unloaded_endpoints():
    async def _run():
        sid = "sess-empty-gates"
        r_prep = await preprocess_dataset(make_request("POST", "/api/preprocess", sid))
        assert r_prep.status_code == 422
        assert run_cluster(make_request("POST", "/api/cluster", sid)).status_code == 422
    asyncio.run(_run())


def test_full_canonical_k3_workflow():
    async def _run():
        sid = "sess-canonical-k3"

        # Step 1: Load sample
        r_sample = load_sample(make_request("POST", "/api/dataset/sample", sid))
        assert r_sample.status_code == 200
        cookie_str = r_sample.headers.get("set-cookie", "")
        m = re.search(r"customerinsight_session=([a-f0-9]+)", cookie_str)
        real_sid = m.group(1) if m else sid

        # Step 2: Preprocess
        r_eda_page = eda_page(make_request("GET", "/eda", real_sid))
        assert r_eda_page.status_code == 200
        r_prep = await preprocess_dataset(make_request("POST", "/api/preprocess", real_sid))
        assert r_prep.status_code == 200
        st_prep = json.loads(r_prep.body)
        assert st_prep["preprocessed"] is True
        assert st_prep["workflow_progress"]["completed_steps"] == 2
        assert st_prep["workflow_progress"]["percent"] == 40

        # Step 3: Choose K
        r_k_page = choose_k_page(make_request("GET", "/choose-k", real_sid))
        assert r_k_page.status_code == 200
        r_k_ana = await run_k_analysis(make_request("POST", "/api/k-analysis", real_sid))
        assert r_k_ana.status_code == 200
        st_k = json.loads(r_k_ana.body)
        assert st_k["k_analysis_data"]["recommended_k"] == 3

        sel_body = json.dumps({"selected_k": 3}).encode("utf-8")
        r_sel_k = await select_k(make_request("POST", "/api/select-k", real_sid, body_bytes=sel_body))
        assert r_sel_k.status_code == 200
        st_sel = json.loads(r_sel_k.body)
        assert st_sel["selected_k"] == 3
        assert st_sel["workflow_progress"]["completed_steps"] == 3
        assert st_sel["workflow_progress"]["percent"] == 60

        # Step 4: Clustering
        r_clust_page = clustering_page(make_request("GET", "/clustering", real_sid))
        assert r_clust_page.status_code == 200
        r_clust = run_cluster(make_request("POST", "/api/cluster", real_sid))
        assert r_clust.status_code == 200
        st_clust = json.loads(r_clust.body)
        assert st_clust["clustered"] is True
        assert st_clust["results_ready"] is True
        assert st_clust["workflow_progress"]["completed_steps"] == 5
        assert st_clust["workflow_progress"]["percent"] == 100

        # Step 5: Results & Verification
        r_res_page = results_page(make_request("GET", "/results", real_sid))
        assert r_res_page.status_code == 200
        r_res = get_results_data(make_request("GET", "/api/results", real_sid))
        assert r_res.status_code == 200
        res = json.loads(r_res.body)

        meta = res["run_metadata"]
        assert abs(meta["inertia"] - 611.4205) < 0.01
        assert abs(meta["silhouette"] - 0.4588) < 0.01
        assert meta["iterations"] == 9
        counts = [p["count"] for p in res["cluster_profiles"]]
        assert sorted(counts) == [159, 173, 388]

        # Step 6: CSV Export
        r_exp = export_results_csv(make_request("GET", "/api/export", real_sid))
        assert r_exp.status_code == 200
        assert r_exp.body.startswith(b"\xef\xbb\xbf")
        lines = [l for l in r_exp.body.decode("utf-8-sig").splitlines() if l.strip()]
        assert lines[0] == "CustomerID,Recency,Frequency,Monetary,Cluster,SegmentName"
        assert len(lines) == 721

    asyncio.run(_run())


def test_dynamic_k5_workflow():
    async def _run():
        sid = "sess-dynamic-k5"
        r_sample = load_sample(make_request("POST", "/api/dataset/sample", sid))
        cookie_str = r_sample.headers.get("set-cookie", "")
        m = re.search(r"customerinsight_session=([a-f0-9]+)", cookie_str)
        real_sid = m.group(1) if m else sid

        await preprocess_dataset(make_request("POST", "/api/preprocess", real_sid))
        await run_k_analysis(make_request("POST", "/api/k-analysis", real_sid))

        sel_body = json.dumps({"selected_k": 5}).encode("utf-8")
        r_sel = await select_k(make_request("POST", "/api/select-k", real_sid, body_bytes=sel_body))
        assert r_sel.status_code == 200

        r_clust = run_cluster(make_request("POST", "/api/cluster", real_sid))
        assert r_clust.status_code == 200

        r_res = get_results_data(make_request("GET", "/api/results", real_sid))
        assert r_res.status_code == 200
        res = json.loads(r_res.body)
        assert len(res["cluster_profiles"]) == 5
        assert res["run_metadata"]["k"] == 5

    asyncio.run(_run())


def test_session_isolation():
    sid_a = "sess-isolation-a"
    sid_b = "sess-isolation-b"

    # Load dataset in session A
    load_sample(make_request("POST", "/api/dataset/sample", sid_a))

    # Session B must remain empty
    r_state_b = get_state(make_request("GET", "/api/state", sid_b))
    st_b = json.loads(r_state_b.body)
    assert st_b["dataset_loaded"] is False


def _http_full_workflow(client: TestClient, strategy: str = "iqr_clip") -> dict:
    assert client.post("/api/dataset/sample").status_code == 200
    preprocess = client.post("/api/preprocess", json={"outlier_strategy": strategy})
    assert preprocess.status_code == 200
    assert client.post("/api/k-analysis", json={"k_min": 2, "k_max": 10}).status_code == 200
    assert client.post("/api/select-k", json={"selected_k": 3}).status_code == 200
    clustered = client.post("/api/cluster")
    assert clustered.status_code == 200
    return clustered.json()


def test_http_default_and_keep_end_to_end_contracts() -> None:
    with TestClient(app) as default_client:
        assert default_client.post("/api/dataset/sample").status_code == 200
        default_state = default_client.post("/api/preprocess").json()
        assert default_state["outlier_strategy"] == "iqr_clip"
        assert default_state["eda_data"]["iqr_applied"] is True

    with TestClient(app) as keep_client:
        state = _http_full_workflow(keep_client, "keep")
        assert state["outlier_strategy"] == "keep"
        assert state["results_ready"] is True
        assert state["eda_data"]["iqr_applied"] is False
        assert all(item["pct_clipped"] == 0 for item in state["eda_data"]["before_after"].values())
        results = keep_client.get("/api/results").json()
        metadata = results["run_metadata"]
        assert metadata["inertia"] == pytest.approx(882.5146, abs=0.01)
        assert metadata["silhouette"] == pytest.approx(0.4502, abs=0.001)
        assert metadata["iterations"] == 11


def test_strategy_change_and_invalid_strategy_are_transactional() -> None:
    with TestClient(app) as client:
        complete = _http_full_workflow(client)
        invalid = client.post("/api/preprocess", json={"outlier_strategy": "winsorize"})
        assert invalid.status_code == 422
        after_invalid = client.get("/api/state").json()
        for key in ("preprocessing_signature", "selected_k", "clustering_data"):
            assert after_invalid[key] == complete[key]
        assert after_invalid["results_ready"] is True

        changed = client.post("/api/preprocess", json={"outlier_strategy": "keep"})
        assert changed.status_code == 200
        state = changed.json()
        assert state["outlier_strategy"] == "keep"
        assert state["preprocessed"] is True
        assert state["k_analyzed"] is False
        assert state["selected_k"] is None
        assert state["clustered"] is False
        assert state["results_ready"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {"max_iter": True}, {"max_iter": 3.5}, {"max_iter": 0},
        {"max_iter": -1}, {"tol": True}, {"tol": float("nan")},
        {"tol": float("inf")}, {"tol": float("-inf")}, {"tol": 0},
        {"tol": -0.1}, {"foo": 123},
    ],
)
def test_invalid_solver_preferences_preserve_valid_workflow(payload: dict) -> None:
    with TestClient(app) as client:
        before = _http_full_workflow(client)
        if any(isinstance(value, float) and not math.isfinite(value) for value in payload.values()):
            token = next(value for value in payload.values() if isinstance(value, float))
            literal = "NaN" if math.isnan(token) else ("Infinity" if token > 0 else "-Infinity")
            response = client.post(
                "/api/solver-preferences",
                content=f'{{"tol": {literal}}}',
                headers={"Content-Type": "application/json"},
            )
        else:
            response = client.post("/api/solver-preferences", json=payload)
        assert response.status_code == 422
        after = client.get("/api/state").json()
        assert after["solver_preferences"] == before["solver_preferences"]
        assert after["results_ready"] is True
        assert after["clustering_data"] == before["clustering_data"]


def test_solver_preferences_merge_invalidate_only_clustering_and_are_idempotent() -> None:
    with TestClient(app) as client:
        before = _http_full_workflow(client)
        same = client.post("/api/solver-preferences", json={"max_iter": 300, "tol": 0.0001})
        assert same.status_code == 200
        assert same.json()["results_ready"] is True

        changed = client.post("/api/solver-preferences", json={"max_iter": 400})
        assert changed.status_code == 200
        state = changed.json()
        assert state["solver_preferences"] == {"max_iter": 400, "tol": 0.0001}
        assert state["preprocessing_signature"] == before["preprocessing_signature"]
        assert state["k_analyzed"] is True
        assert state["selected_k"] == 3
        assert state["clustered"] is False
        assert state["results_ready"] is False


def test_real_missing_and_zero_outlier_counts_have_no_demo_fallback() -> None:
    csv_data = (
        "CustomerID,Recency,Frequency,Monetary\n"
        "C1,0,1,10\nC2,,2,20\nC3,2,3,30\nC4,3,4,40\n"
    )
    with TestClient(app) as client:
        uploaded = client.post(
            "/api/dataset/upload",
            files={"file": ("customers.csv", csv_data, "text/csv")},
        )
        assert uploaded.status_code == 200
        raw_state = uploaded.json()
        assert raw_state["eda_data"]["missing_count"] == 1
        processed = client.post("/api/preprocess", json={"outlier_strategy": "keep"})
        assert processed.status_code == 200
        assert processed.json()["eda_data"]["missing_count"] == 1
        assert processed.json()["eda_data"]["total_outliers"] == 0


def test_tv5_configuration_is_session_isolated() -> None:
    with TestClient(app) as first, TestClient(app) as second:
        first.post("/api/dataset/sample")
        first.post("/api/preprocess", json={"outlier_strategy": "keep"})
        first.post("/api/solver-preferences", json={"max_iter": 450, "tol": 0.0002})
        first_state = first.get("/api/state").json()
        second_state = second.get("/api/state").json()
        assert first_state["outlier_strategy"] == "keep"
        assert first_state["solver_preferences"] == {"max_iter": 450, "tol": 0.0002}
        assert second_state["dataset_loaded"] is False
        assert second_state["outlier_strategy"] == "iqr_clip"
        assert second_state["solver_preferences"] == {"max_iter": 300, "tol": 0.0001}


def test_tv5_ui_and_business_interpretation_regression_guards() -> None:
    root = Path(__file__).resolve().parents[1]
    eda_js = (root / "web/static/js/eda.js").read_text(encoding="utf-8")
    clustering_js = (root / "web/static/js/clustering.js").read_text(encoding="utf-8")
    eda_html = (root / "web/templates/eda.html").read_text(encoding="utf-8")
    clustering_html = (root / "web/templates/clustering.html").read_text(encoding="utf-8")
    app_source = (root / "web/app.py").read_text(encoding="utf-8")

    assert "|| 117" not in eda_js
    assert "|| 720" not in eda_js + clustering_js
    assert "117" not in eda_html
    assert "720" not in eda_html + clustering_html
    assert "Sau Median Imputation / Keep" in eda_js
    assert "Không áp dụng IQR clipping" in eda_js
    assert "generate_business_interpretation(state.cluster_profiles)" in app_source
    assert "r_mean <= 50" not in app_source
    assert "r_mean > 100" not in app_source
