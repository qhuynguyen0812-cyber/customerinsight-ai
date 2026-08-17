"""FastAPI entry point for the isolated Stitch UI prototype."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from components.results_export import customer_results_to_csv_bytes
from components.workflow import WorkflowStage, workflow_stage
from src.clustering import analyze_candidate_k, recommend_k
from src.preprocessing import PreprocessingError, run_pipeline_preprocessing
from src.profiling import run_clustering_workflow
from src.state import set_k_analysis, set_preprocessed_data, set_raw_dataset, set_selected_k
from src.validation import DataValidationError, ValidatedDataset, load_csv_bytes, load_sample_dataset
from web.session_store import BrowserSession, session_store

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
SESSION_COOKIE = "customerinsight_session"

app = FastAPI(title="CustomerInsight AI", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


def _session(request: Request) -> tuple[str, BrowserSession]:
    return session_store.get(request.cookies.get(SESSION_COOKIE))


def _with_session(response: Response, session_id: str):
    response.set_cookie(SESSION_COOKIE, session_id, httponly=True, samesite="lax")
    return response


def _commit(session: BrowserSession, dataset: ValidatedDataset) -> None:
    set_raw_dataset(session.app_state, dataset.raw_df, dataset.dataset_signature)
    session.quality_report = dataset.quality_report


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _state_payload(session: BrowserSession) -> dict[str, Any]:
    state = session.app_state
    loaded = state.raw_df is not None
    preprocessed = state.processed_df is not None
    k_analyzed = state.k_metrics is not None
    k_selected = state.selected_k is not None
    clustered = state.model is not None and state.cluster_profiles is not None
    results_ready = clustered and state.results is not None

    preview = []
    if loaded:
        preview = [
            {key: _json_value(value) for key, value in row.items()}
            for row in state.raw_df.head(8).to_dict(orient="records")
        ]

    stage = workflow_stage(state)
    completed = int(stage)
    next_step_map = {
        WorkflowStage.EMPTY: "Dữ liệu",
        WorkflowStage.DATA_READY: "Khám phá dữ liệu",
        WorkflowStage.PREPROCESSED: "Chọn K",
        WorkflowStage.K_CONFIRMED: "Phân cụm",
        WorkflowStage.CLUSTERED: "Kết quả",
        WorkflowStage.RESULTS_READY: "Phân tích hoàn tất",
    }
    next_step = next_step_map.get(stage, "Dữ liệu")

    eda_data = None
    if loaded:
        raw_df = state.raw_df
        if preprocessed and state.processed_df is not None:
            proc_df = state.processed_df
            bounds_dict = state.eda_summary.get("iqr_bounds", {}) if state.eda_summary else {}

            # Pearson correlation on processed features
            corr_df = proc_df[["Recency", "Frequency", "Monetary"]].corr()
            corr_matrix = {
                "Recency": {
                    "Recency": round(float(corr_df.loc["Recency", "Recency"]), 2),
                    "Frequency": round(float(corr_df.loc["Recency", "Frequency"]), 2),
                    "Monetary": round(float(corr_df.loc["Recency", "Monetary"]), 2),
                },
                "Frequency": {
                    "Recency": round(float(corr_df.loc["Frequency", "Recency"]), 2),
                    "Frequency": round(float(corr_df.loc["Frequency", "Frequency"]), 2),
                    "Monetary": round(float(corr_df.loc["Frequency", "Monetary"]), 2),
                },
                "Monetary": {
                    "Recency": round(float(corr_df.loc["Monetary", "Recency"]), 2),
                    "Frequency": round(float(corr_df.loc["Monetary", "Frequency"]), 2),
                    "Monetary": round(float(corr_df.loc["Monetary", "Monetary"]), 2),
                },
            }

            # Before / After outlier comparisons
            before_after = {}
            for col in ["Recency", "Frequency", "Monetary"]:
                raw_col = raw_df[col]
                proc_col = proc_df[col]
                raw_max = float(raw_col.max())
                proc_max = float(proc_col.max())
                raw_median = float(raw_col.median())
                proc_median = float(proc_col.median())
                b = bounds_dict.get(col, {})
                outliers = int(session.quality_report.iqr_outlier_by_column.get(col, 0)) if session.quality_report else 0
                pct_clipped = round((raw_max - proc_max) / raw_max * 100, 1) if raw_max > proc_max else 0.0
                before_after[col] = {
                    "raw_max": raw_max,
                    "clipped_max": proc_max,
                    "raw_median": raw_median,
                    "proc_median": proc_median,
                    "pct_clipped": pct_clipped,
                    "outliers": outliers,
                    "q1": float(b.get("q1", 0)),
                    "q3": float(b.get("q3", 0)),
                    "iqr": float(b.get("iqr", 0)),
                    "lower_bound": float(b.get("lower_bound", 0)),
                    "upper_bound": float(b.get("upper_bound", 0)),
                }

            # Descriptive statistics table
            desc_raw = raw_df[["Recency", "Frequency", "Monetary"]].describe().to_dict()
            desc_proc = proc_df[["Recency", "Frequency", "Monetary"]].describe().to_dict()
            stats_table = {
                "raw": {col: {k: round(float(v), 2) for k, v in desc_raw[col].items()} for col in ["Recency", "Frequency", "Monetary"]},
                "processed": {col: {k: round(float(v), 2) for k, v in desc_proc[col].items()} for col in ["Recency", "Frequency", "Monetary"]},
            }

            # Chart distribution arrays for Plotly
            chart_data = {
                "Recency": {"raw": raw_df["Recency"].tolist(), "processed": proc_df["Recency"].tolist()},
                "Frequency": {"raw": raw_df["Frequency"].tolist(), "processed": proc_df["Frequency"].tolist()},
                "Monetary": {"raw": raw_df["Monetary"].tolist(), "processed": proc_df["Monetary"].tolist()},
            }

            eda_data = {
                "row_count": int(len(proc_df)),
                "feature_count": 3,
                "missing_count": 0,
                "total_outliers": sum(item["outliers"] for item in before_after.values()),
                "before_after": before_after,
                "correlation": corr_matrix,
                "stats_table": stats_table,
                "chart_data": chart_data,
            }
        else:
            eda_data = {
                "row_count": int(len(raw_df)),
                "feature_count": 3,
                "missing_count": 0,
                "raw_medians": {col: float(raw_df[col].median()) for col in ["Recency", "Frequency", "Monetary"]},
                "raw_maxes": {col: float(raw_df[col].max()) for col in ["Recency", "Frequency", "Monetary"]},
            }

    k_data = None
    if k_analyzed and state.k_metrics is not None:
        if isinstance(state.k_metrics, dict):
            k_list = state.k_metrics.get("k", [])
            inertia_list = state.k_metrics.get("inertia", [])
            silhouette_list = state.k_metrics.get("silhouette", [])
            metrics_records = [
                {
                    "k": int(k_list[i]),
                    "inertia": round(float(inertia_list[i]), 4),
                    "silhouette": round(float(silhouette_list[i]), 4),
                }
                for i in range(len(k_list))
            ]
        elif hasattr(state.k_metrics, "to_dict"):
            metrics_records = [
                {
                    "k": int(row["k"]),
                    "inertia": round(float(row["inertia"]), 4),
                    "silhouette": round(float(row["silhouette"]), 4),
                }
                for row in state.k_metrics.to_dict(orient="records")
            ]
        else:
            metrics_records = []

        k_data = {
            "k_metrics": metrics_records,
            "recommended_k": int(state.recommended_k) if state.recommended_k is not None else None,
            "selected_k": int(state.selected_k) if state.selected_k is not None else None,
            "k_min": int(min(r["k"] for r in metrics_records)) if metrics_records else None,
            "k_max": int(max(r["k"] for r in metrics_records)) if metrics_records else None,
        }

    clustering_data = None
    if clustered and state.cluster_profiles is not None:
        profiles_list = []
        for idx, row in state.cluster_profiles.iterrows():
            c_id = int(row["Cluster"])
            cnt = int(row["count"])
            pct = round(float(row["percentage"]), 1)
            r_mean = round(float(row["mean Recency"]), 2)
            f_mean = round(float(row["mean Frequency"]), 2)
            m_mean = round(float(row["mean Monetary"]), 2)
            seg = str(row["SegmentName"])

            rec = (
                "Ưu tiên duy trì tương tác và cân nhắc cơ hội gia tăng giá trị."
                if r_mean <= 50 and m_mean >= 1000
                else (
                    "Cân nhắc chiến dịch nuôi dưỡng hoặc tái kích hoạt phù hợp."
                    if r_mean > 100
                    else "Duy trì tần suất mua hàng và nâng cao mức độ gắn kết."
                )
            )

            profiles_list.append({
                "cluster_id": c_id,
                "cluster_label": f"Cluster {c_id + 1:02d}",
                "count": cnt,
                "percentage": pct,
                "mean_recency": r_mean,
                "mean_frequency": f_mean,
                "mean_monetary": m_mean,
                "segment_name": seg,
                "recommendation": rec,
            })

        points_2d = []
        centers_list = []
        try:
            from sklearn.decomposition import PCA
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(state.scaled_matrix)
            x_min, x_max = float(coords[:, 0].min()), float(coords[:, 0].max())
            y_min, y_max = float(coords[:, 1].min()), float(coords[:, 1].max())
            x_span = x_max - x_min if x_max != x_min else 1.0
            y_span = y_max - y_min if y_max != y_min else 1.0

            x_norm = ((coords[:, 0] - x_min) / x_span) * 80.0 + 10.0
            y_norm = ((coords[:, 1] - y_min) / y_span) * 80.0 + 10.0

            centers_2d = pca.transform(state.model.cluster_centers_)
            cx_norm = ((centers_2d[:, 0] - x_min) / x_span) * 80.0 + 10.0
            cy_norm = ((centers_2d[:, 1] - y_min) / y_span) * 80.0 + 10.0

            points_2d = [
                {"x": round(float(x_norm[i]), 2), "y": round(float(y_norm[i]), 2), "cluster": int(state.labels[i])}
                for i in range(len(state.labels))
            ]
            centers_list = [
                {"x": round(float(cx_norm[i]), 2), "y": round(float(cy_norm[i]), 2), "cluster": i}
                for i in range(len(centers_2d))
            ]
        except Exception:
            pass

        meta = state.run_metadata or {}
        clustering_data = {
            "k": int(state.selected_k) if state.selected_k is not None else len(profiles_list),
            "inertia": round(float(meta.get("inertia", 0.0)), 4),
            "silhouette": round(float(meta.get("silhouette", 0.0)), 4),
            "iterations": int(meta.get("iterations", 0)),
            "runtime_seconds": round(float(meta.get("runtime_seconds", 0.0)), 2),
            "init": str(meta.get("init", "k-means++")),
            "n_init": int(meta.get("n_init", 10)),
            "random_state": int(meta.get("random_state", 42)),
            "max_iter": int(meta.get("max_iter", 300)),
            "tol": float(meta.get("tol", 0.0001)),
            "profiles": profiles_list,
            "points_2d": points_2d,
            "centers_2d": centers_list,
            "row_count": len(state.labels) if state.labels is not None else 0,
        }

    return {
        "dataset_loaded": loaded,
        "preprocessed": preprocessed,
        "k_analyzed": k_analyzed,
        "k_selected": k_selected,
        "clustered": clustered,
        "results_ready": results_ready,
        "selected_k": state.selected_k,
        "row_count": int(len(state.raw_df)) if loaded else 0,
        "dataset_signature": state.dataset_signature,
        "preprocessing_signature": state.preprocessing_signature,
        "quality_report": asdict(session.quality_report) if session.quality_report else None,
        "workflow_progress": {
            "completed_steps": completed,
            "total_steps": 5,
            "percent": completed * 20,
            "next_step": next_step,
        },
        "preview": preview,
        "eda_data": eda_data,
        "k_analysis_data": k_data,
        "clustering_data": clustering_data,
    }


@app.get("/", include_in_schema=False)
def overview(request: Request):
    session_id, _ = _session(request)
    return _with_session(FileResponse(WEB / "templates" / "overview.html"), session_id)


@app.get("/data", include_in_schema=False)
def data_page(request: Request):
    session_id, _ = _session(request)
    return _with_session(FileResponse(WEB / "templates" / "data.html"), session_id)


@app.get("/eda", include_in_schema=False)
def eda_page(request: Request):
    session_id, session = _session(request)
    if session.app_state.raw_df is None:
        return _with_session(RedirectResponse(url="/data", status_code=303), session_id)
    return _with_session(FileResponse(WEB / "templates" / "eda.html"), session_id)


@app.get("/choose-k", include_in_schema=False)
def choose_k_page(request: Request):
    session_id, session = _session(request)
    if session.app_state.processed_df is None:
        return _with_session(RedirectResponse(url="/eda", status_code=303), session_id)
    return _with_session(FileResponse(WEB / "templates" / "choose_k.html"), session_id)


@app.get("/clustering", include_in_schema=False)
def clustering_page(request: Request):
    session_id, session = _session(request)
    if session.app_state.selected_k is None:
        return _with_session(RedirectResponse(url="/choose-k", status_code=303), session_id)
    return _with_session(FileResponse(WEB / "templates" / "clustering.html"), session_id)


@app.get("/results", include_in_schema=False)
def results_page(request: Request):
    session_id, session = _session(request)
    state = session.app_state
    if state.results is None or state.cluster_profiles is None or state.run_metadata is None:
        return _with_session(RedirectResponse(url="/clustering", status_code=303), session_id)
    return _with_session(FileResponse(WEB / "templates" / "results.html"), session_id)


@app.get("/api/state")
def get_state(request: Request):
    session_id, session = _session(request)
    return _with_session(JSONResponse(_state_payload(session)), session_id)


@app.get("/api/results")
def get_results_data(request: Request):
    session_id, session = _session(request)
    state = session.app_state
    if state.results is None or state.cluster_profiles is None or state.run_metadata is None:
        return _with_session(JSONResponse({"detail": "Chưa có kết quả phân tích."}, status_code=422), session_id)

    profiles_list = []
    counts_and_percentages = {"all": int(len(state.results))}
    for idx, row in state.cluster_profiles.iterrows():
        c_id = int(row["Cluster"])
        cnt = int(row["count"])
        pct = round(float(row["percentage"]), 1)
        r_mean = round(float(row["mean Recency"]), 2)
        f_mean = round(float(row["mean Frequency"]), 2)
        m_mean = round(float(row["mean Monetary"]), 2)
        seg = str(row["SegmentName"])
        counts_and_percentages[str(c_id)] = cnt

        rec = (
            "Frequency và Monetary trung bình cao nhất."
            if r_mean <= 50 and m_mean >= 1000
            else (
                "Recency trung bình lớn nhất."
                if r_mean > 100
                else "Phân khúc có quy mô lớn nhất."
            )
        )

        profiles_list.append({
            "cluster_id": c_id,
            "cluster_label": f"Cluster {c_id + 1:02d}",
            "count": cnt,
            "percentage": pct,
            "mean_recency": r_mean,
            "mean_frequency": f_mean,
            "mean_monetary": m_mean,
            "segment_name": seg,
            "insight": rec,
        })

    customers_list = [
        {
            "id": str(row["CustomerID"]),
            "r": _json_value(row["Recency"]),
            "f": _json_value(row["Frequency"]),
            "m": _json_value(row["Monetary"]),
            "cluster": int(row["Cluster"]),
            "name": str(row["SegmentName"]),
        }
        for _, row in state.results.iterrows()
    ]

    meta = state.run_metadata or {}
    results_payload = {
        "selected_k": int(state.selected_k) if state.selected_k is not None else len(profiles_list),
        "row_count": int(len(state.results)),
        "cluster_profiles": profiles_list,
        "counts_and_percentages": counts_and_percentages,
        "run_metadata": {
            "k": int(meta.get("k", state.selected_k or len(profiles_list))),
            "init": str(meta.get("init", "k-means++")),
            "n_init": int(meta.get("n_init", 10)),
            "random_state": int(meta.get("random_state", 42)),
            "max_iter": int(meta.get("max_iter", 300)),
            "tol": float(meta.get("tol", 0.0001)),
            "inertia": round(float(meta.get("inertia", 0.0)), 4),
            "silhouette": round(float(meta.get("silhouette", 0.0)), 4),
            "iterations": int(meta.get("iterations", 0)),
            "runtime_seconds": round(float(meta.get("runtime_seconds", 0.0)), 2),
        },
        "customer_results": customers_list,
        "workflow_progress": {
            "completed_steps": 5,
            "total_steps": 5,
            "percent": 100,
            "next_step": "Phân tích hoàn tất",
        },
    }
    return _with_session(JSONResponse(results_payload), session_id)


@app.get("/api/export")
def export_results_csv(request: Request):
    session_id, session = _session(request)
    state = session.app_state
    if state.results is None:
        return _with_session(JSONResponse({"detail": "Chưa có kết quả phân tích để xuất."}, status_code=422), session_id)

    csv_data = customer_results_to_csv_bytes(state.results)
    response = Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="customer_results.csv"',
        },
    )
    return _with_session(response, session_id)


@app.post("/api/dataset/sample")
def load_sample(request: Request):
    session_id, session = _session(request)
    try:
        dataset = load_sample_dataset(ROOT / "data" / "sample_customers.csv")
        _commit(session, dataset)
        response = JSONResponse(_state_payload(session))
    except DataValidationError as exc:
        response = JSONResponse({"detail": str(exc)}, status_code=422)
    return _with_session(response, session_id)


@app.post("/api/dataset/upload")
async def upload_dataset(request: Request, file: UploadFile = File(...)):
    session_id, session = _session(request)
    try:
        dataset = load_csv_bytes(await file.read())
        _commit(session, dataset)
        response = JSONResponse(_state_payload(session))
    except DataValidationError as exc:
        response = JSONResponse({"detail": str(exc)}, status_code=422)
    return _with_session(response, session_id)


@app.post("/api/preprocess")
def preprocess_dataset(request: Request):
    session_id, session = _session(request)
    if session.app_state.raw_df is None:
        return _with_session(JSONResponse({"detail": "Chưa tải dữ liệu. Vui lòng tải dữ liệu trước khi tiền xử lý."}, status_code=422), session_id)
    try:
        result = run_pipeline_preprocessing(session.app_state.raw_df)
        set_preprocessed_data(
            session.app_state,
            result["processed_df"],
            result["scaled_matrix"],
            result["preprocessing_signature"],
            result["eda_summary"],
        )
        response = JSONResponse(_state_payload(session))
    except (PreprocessingError, Exception) as exc:
        response = JSONResponse({"detail": str(exc)}, status_code=422)
    return _with_session(response, session_id)


@app.post("/api/k-analysis")
async def run_k_analysis(request: Request):
    session_id, session = _session(request)
    if session.app_state.scaled_matrix is None:
        return _with_session(JSONResponse({"detail": "Cần thực hiện tiền xử lý dữ liệu trước khi phân tích K."}, status_code=422), session_id)

    k_min = 2
    k_max = 10
    try:
        if request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
            if "k_min" in body:
                k_min = int(body["k_min"])
            if "k_max" in body:
                k_max = int(body["k_max"])
        else:
            params = request.query_params
            if "k_min" in params:
                k_min = int(params["k_min"])
            if "k_max" in params:
                k_max = int(params["k_max"])
    except Exception:
        pass

    try:
        k_metrics = analyze_candidate_k(session.app_state.scaled_matrix, k_min=k_min, k_max=k_max)
        recommended_k = recommend_k(k_metrics)
        set_k_analysis(session.app_state, k_metrics, recommended_k)
        response = JSONResponse(_state_payload(session))
    except Exception as exc:
        response = JSONResponse({"detail": str(exc)}, status_code=422)
    return _with_session(response, session_id)


@app.post("/api/select-k")
async def select_k(request: Request):
    session_id, session = _session(request)
    if session.app_state.k_metrics is None:
        return _with_session(JSONResponse({"detail": "Cần thực hiện phân tích K trước khi chọn K."}, status_code=422), session_id)

    selected_k_val = None
    try:
        if request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
            selected_k_val = int(body.get("selected_k"))
        else:
            params = request.query_params
            if "selected_k" in params:
                selected_k_val = int(params["selected_k"])
    except Exception:
        pass

    if selected_k_val is None:
        return _with_session(JSONResponse({"detail": "Vui lòng cung cấp giá trị selected_k hợp lệ."}, status_code=422), session_id)

    try:
        k_list = session.app_state.k_metrics.get("k", []) if isinstance(session.app_state.k_metrics, dict) else list(session.app_state.k_metrics["k"])
        if selected_k_val not in k_list:
            return _with_session(JSONResponse({"detail": f"K = {selected_k_val} không nằm trong danh sách các giá trị K đã phân tích."}, status_code=422), session_id)

        set_selected_k(session.app_state, selected_k_val)
        response = JSONResponse(_state_payload(session))
    except Exception as exc:
        response = JSONResponse({"detail": str(exc)}, status_code=422)
    return _with_session(response, session_id)


@app.post("/api/cluster")
def run_cluster(request: Request):
    session_id, session = _session(request)
    state = session.app_state
    if state.scaled_matrix is None:
        return _with_session(JSONResponse({"detail": "Cần tiền xử lý dữ liệu trước khi phân cụm."}, status_code=422), session_id)
    if state.selected_k is None:
        return _with_session(JSONResponse({"detail": "Cần xác nhận số cụm K trước khi phân cụm."}, status_code=422), session_id)
    if state.raw_df is None:
        return _with_session(JSONResponse({"detail": "Chưa có dữ liệu thô."}, status_code=422), session_id)

    try:
        run_clustering_workflow(state)
        response = JSONResponse(_state_payload(session))
    except Exception as exc:
        response = JSONResponse({"detail": str(exc)}, status_code=422)
    return _with_session(response, session_id)
