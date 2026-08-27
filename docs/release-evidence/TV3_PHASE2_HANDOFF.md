# TV3 Phase 2 Handoff

## Scope

- TV: TV3
- Branch: `phase2/tv3-k-hardening`
- Base: `c0d4a514846b3dcff2b623a5b257cbd40e78e76f` (`origin/develop`, verified after `git fetch --all --prune` on 2026-08-26)
- Requirements: FR-009, FR-010, Phase 2 K hardening and reproducibility
- Input from: TV2 `scaled_matrix`
- Required reviewer: TV4
- TV4 review status: PENDING; no reviewer approval is claimed by this handoff

No production change was required. The current `origin/develop` implementation already satisfies the audited TV3 contract. Phase 2 adds regression evidence only; no existing tests were deleted or weakened.

## Public contract and consumers

Public APIs:

- `analyze_candidate_k(...)`
- `recommend_k(...)`
- `run_kmeans(...)`

The TV4 seam remains the frozen `KMeansResult` contract:

- `model`
- `labels`
- `inertia`
- `iterations`

Backward-compatible `model, labels = run_kmeans(...)` unpacking remains supported. `src/profiling.py` continues to consume all four named fields through `run_clustering_workflow(...)`.

Consumers are TV4 profiling, TV5 API/state integration, and TV6 release QA.

## Scientific evidence

Canonical sample and preprocessing observed on the verified branch:

- Rows: 720
- Features: RFM after median missing handling, IQR clipping, and `StandardScaler`
- Recommended K: 3
- K=3 inertia: `611.4205381920902`
- K=3 silhouette: `0.45877917738169266`
- K=3 iterations: `9`

Dynamic evidence is covered by the complete HTTP workflow in `tests/test_tv6_release_http.py`: selecting K=5 produces a five-cluster model result, exactly five profiles, run metadata K=5, and a current deterministic export. `tests/test_web_api.py` independently covers the K=5 application workflow.

The dedicated Phase 2 evidence also verifies:

- inclusive custom and single-candidate K ranges;
- direct K-Means permits `K == n_samples`, while analysis rejects `k_max >= n_samples` before fitting;
- integer-only K/range values, explicitly excluding booleans;
- numeric, two-dimensional, non-empty, nonzero-feature, finite matrices;
- exact canonical solver defaults and fresh-copy behavior;
- effective `max_iter`/`tol` overrides without default mutation;
- rejection of unsupported solver settings;
- maximum-silhouette recommendation and smaller-K deterministic tie-break;
- rejection of missing, empty, unequal-length, or nonfinite recommendation metrics;
- deterministic labels, inertia, and iterations across identical runs.

## Failure and invalidation behavior

Observed failure behavior is a clear domain `ValueError` or HTTP 422 for invalid range, insufficient samples for silhouette, malformed matrix, invalid direct K, unsupported solver settings, and selecting a K outside the analyzed range.

The HTTP range test analyzes 3 through 6, accepts advisory override K=5, rejects K=8 with HTTP 422, retains the prior valid K=5 selection, and produces no clustering artifacts.

Atomicity and freshness evidence verifies:

- a failed K analysis does not replace prior `k_metrics` or `recommended_k`;
- committing a new valid K analysis retains its new metrics/recommendation and clears selected K, model, labels, profiles, metadata, results, and export;
- changing selected K retains K metrics/recommendation and clears model, labels, profiles, metadata, results, and export;
- results and export endpoints remain blocked until a fresh clustering run completes.

## UI audit

`web/templates/choose_k.html` and `web/static/js/choose_k.js` were audited without modification. The existing UI displays inertia and silhouette, identifies the recommendation, permits a different analyzed K, supports custom ranges, shows backend errors, confirms the selected K, and does not force K=3. No UI redesign or Algorithm page was introduced.

## Test evidence

The repository's `python` launcher and legacy `.venv` are unavailable in this environment, so all successful commands used the repository's valid `.venv-clean` interpreter.

Targeted commands and exact results:

- `.\.venv-clean\Scripts\python.exe -m pytest tests/test_clustering.py -q -ra` — 17 passed, 1 warning, 8.55s
- `.\.venv-clean\Scripts\python.exe -m pytest tests/test_tv3_k_hardening.py -q -ra` — 31 passed, 2 warnings, 5.49s
- `.\.venv-clean\Scripts\python.exe -m pytest tests/test_web_api.py -q -ra` — 8 passed, 1 warning, 9.16s
- `.\.venv-clean\Scripts\python.exe -m pytest tests/test_tv6_release_http.py -q -ra` — 12 passed, 2 warnings, 22.61s
- `.\.venv-clean\Scripts\python.exe -m pytest tests/test_profiling.py -q -ra` — 6 passed, 3.11s

Full gates and exact results:

- `.\.venv-clean\Scripts\python.exe -m pytest -q -ra` — 146 passed, 2 warnings, 22.80s; 0 skipped
- `.\.venv-clean\Scripts\python.exe -m pytest --collect-only -q` — 146 tests collected, 1 warning, 2.89s
- `.\.venv-clean\Scripts\python.exe -m compileall -q src web components tests` — PASS (exit 0, no output)
- `.\.venv-clean\Scripts\python.exe -m pip check` — PASS: `No broken requirements found.`
- `git diff --check` — PASS (exit 0, no output)

Warnings are limited to the existing Starlette `httpx` test-client deprecation and joblib's physical-core detection fallback. There are no failures or skips.

## Contract deviation audit

- `KMeansResult` retained: PASS
- TV4 named-field and workflow compatibility retained: PASS
- tuple-only regression absent: PASS
- existing validation retained: PASS
- tests deleted or assertions weakened: NONE
- production K=3 or canonical metric hard-coding added: NONE
- preprocessing, profiling/business logic, export, or state architecture modified: NONE
- Streamlit or old pages introduced: NONE
- UI redesign introduced: NONE
- arbitrary sklearn kwargs accepted: NO
- stale results/export regression: NONE

`CONTRACT_DEVIATIONS = 0`

## Prepared PR metadata

Title: `phase2(tv3): harden K analysis and preserve clustering contract`

- Base: `develop`
- Head: `phase2/tv3-k-hardening`
- Owner: TV3
- Reviewer: TV4
- UI impact: No redesign; K-analysis behavior only.

Summary for the PR body:

- preserves the `KMeansResult` public contract and deterministic canonical baseline;
- verifies custom K ranges and invalid K/range/sample failures;
- verifies solver overrides without weakening the whitelist;
- verifies dynamic K5, atomic K-analysis failure, and downstream invalidation;
- makes no preprocessing, profile, export, state-architecture, or UI-design changes.

Formal Phase 2 approval remains pending actual TV4 review and green remote PR CI.
