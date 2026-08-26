# TV1 Phase 2 handoff

Observed 2026-08-26 (Asia/Bangkok). This document reports only checks executed on
`phase2/tv1-data-hardening` against the fetched `origin/develop` state.

## Ownership and baseline

- TV: TV1
- Branch: `phase2/tv1-data-hardening`
- Base: `31af46b04419e74d743ddd08908e1d3e8808a486`
- Requirements: FR-001, FR-002, FR-003, FR-004, NFR-002
- Required reviewer: TV2 (review pending; no approval is claimed)

## Changed files

- `tests/test_tv1_data_hardening.py`
- `docs/release-evidence/TV1_PHASE2_HANDOFF.md`

No production code change was required by the audited TV1 contract.

## Verified behavior

- The canonical built-in sample uses the same byte parsing and validation pipeline as
  uploads, loads 720 rows, and has SHA-256
  `622a6cff9d8b41106268eb1e31e50b5259ccc1d4c318a15a5c496c8edce2a96f`.
- CSV uploads normalize required header whitespace and case, discard extra columns from
  canonical `raw_df`, and reject duplicate normalized canonical headers.
- `CustomerID` is required, nonblank, unique, excluded from RFM features, and preserves
  textual identifiers such as `0012` through validation and HTTP state preview.
- Recency, Frequency, and Monetary reject nonnumeric, negative, and infinite values.
- Missing RFM values remain valid and unmodified at the TV1 boundary, are counted in the
  quality report, and serialize as JSON `null` where exposed to the browser.
- The quality report exposes row, missing, duplicate-row, duplicate-customer, nonnumeric,
  negative, infinity, IQR-outlier, and zero-variance measurements. TV1 detects but does
  not clip or impute values.
- Dataset identity is SHA-256 of the original file bytes; byte-different payloads produce
  different signatures.
- Empty, malformed, schema-invalid, identity-invalid, and RFM-domain-invalid uploads
  return HTTP 422 with `{"detail": "..."}` and do not replace the previous dataset.
- Failed uploads preserve the prior signature, row count, preview, completed results,
  and export.
- The data page supports sample loading, file selection, drag/drop upload, validation
  errors, quality totals/table, preview, signature, row count, and valid-data EDA gating.
  Untrusted preview values are HTML-escaped before `innerHTML` insertion.

## Consumers

- TV2 preprocessing
- TV5 state/FastAPI integration
- TV6 release QA

## Tests and observed results

Executed with `.venv-clean\Scripts\python.exe` consistently:

```text
.venv-clean\Scripts\python.exe -m pytest tests/test_validation.py -q -ra
16 passed in 12.48s

.venv-clean\Scripts\python.exe -m pytest tests/test_tv1_data_hardening.py -q -ra
8 passed in 47.20s

.venv-clean\Scripts\python.exe -m pytest tests/test_web_api.py -q -ra
8 passed, 1 warning in 10.22s

.venv-clean\Scripts\python.exe -m pytest tests/test_tv6_release_http.py -q -ra
12 passed, 2 warnings in 27.12s

.venv-clean\Scripts\python.exe -m pytest -q -ra
115 passed, 2 warnings in 37.20s

.venv-clean\Scripts\python.exe -m pytest --collect-only -q
115 tests collected, 1 warning in 2.22s

.venv-clean\Scripts\python.exe -m compileall -q src web components tests
PASS (exit 0, no output)

.venv-clean\Scripts\python.exe -m pip check
No broken requirements found.

git diff --check
PASS (exit 0, no output)
```

Observed warnings are Starlette's TestClient/httpx deprecation warning and joblib's
physical-core detection fallback.

## Contract-deviation audit

`CONTRACT_DEVIATIONS = 0`

The branch does not reintroduce Streamlit or Phase 1 UI, move preprocessing into TV1,
change K analysis/K-Means, profiling, solver configuration, workflow architecture,
results/export design, or external AI/cloud behavior. It does not hard-code K=3 or
canonical metrics in production, delete tests, weaken assertions, or change unrelated
source files. Stale-results and stale-export preservation tests pass.

## Known limitations

- TV2 review has not yet occurred.
- Remote PR checks/CI have not been run because no PR was created or pushed in this task.
- The passing test run emits the two existing environment/deprecation warnings documented
  above.
