# CustomerInsight AI

Customer Segmentation using K-Means — AI Final Project.

## Authority

1. Đề bài cuối kỳ của giảng viên.
2. `CustomerInsight_AI_Implementation_Ready_Package_v1.1_TeamExecution` (locked implementation contract).
3. Tài liệu môn học.
4. Source code + tests.

Code khác contract thì dừng và báo issue; không tự đoán behavior.

## Runtime

- Windows 10/11
- Python 3.11.x
- FastAPI + Uvicorn (Web Frontend & API)
- Chrome/Edge

## Canonical input

```text
CustomerID
Recency
Frequency
Monetary
```

`CustomerID` chỉ dùng định danh/mapping, không đưa vào K-Means.

## Canonical pipeline

```text
Raw CSV
→ Validation
→ Missing = Median
→ Outlier = IQR clipping / Winsorization
→ StandardScaler(R,F,M)
→ Elbow + Silhouette
→ Người dùng xác nhận K
→ K-Means++
→ Cluster Profiles
→ Business Interpretation
→ Export
```

## Team workflow

Integration branch: `develop`.

Feature branches (chỉ tạo sau khi approved baseline đã có canonical dataset):

```text
feature/tv1-data-validation
feature/tv2-preprocessing-eda
feature/tv3-k-analysis
feature/tv4-clustering-profiling
feature/tv5-workflow-state
feature/tv6-results-qa
```

Review pairs:

```text
TV1 ↔ TV2
TV3 ↔ TV4
TV5 ↔ TV6
```

Không commit trực tiếp vào `main` hoặc `develop` trong thời gian implementation.

## Project structure

```text
customerinsight-ai/
├── web/
│   ├── app.py          # FastAPI application & API endpoints
│   ├── templates/       # HTML templates (Stitch visual parity)
│   └── static/          # CSS design tokens & JavaScript modules
├── components/         # Shared state & workflow helpers
├── src/                # Canonical scientific core logic
├── data/               # Canonical datasets
├── tests/              # PyTest test suite
├── docs/               # Specifications & release evidence
├── requirements.txt
├── README.md
└── .gitignore
```

## Setup & Running

1. Khởi tạo môi trường ảo và cài đặt dependencies:
```cmd
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Khởi chạy ứng dụng Web (FastAPI):
```cmd
.\.venv\Scripts\python.exe -m uvicorn web.app:app --reload
```
Truy cập giao diện tại: `http://127.0.0.1:8000`

## Verification

```cmd
.\.venv\Scripts\python.exe -m pytest -q -ra
.\.venv\Scripts\python.exe -m pytest --collect-only -q
.\.venv\Scripts\python.exe -m compileall -q web src components tests
.\.venv\Scripts\python.exe -m pip check
```

## Baseline lock

Canonical sample expected by the locked package:

```text
Rows          = 720
Mapping       = 720/720
Recommended K = 3
Inertia       ≈ 611.4205381920901
Silhouette    ≈ 0.45877917738169266
Iterations    = 9
SHA-256       = 622a6cff9d8b41106268eb1e31e50b5259ccc1d4c318a15a5c496c8edce2a96f
```

**Do not hard-code these metrics.** The canonical CSV must be verified by SHA-256 before the team branches are created.
