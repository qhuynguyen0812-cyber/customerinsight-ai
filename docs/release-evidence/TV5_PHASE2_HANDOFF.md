# TV5 Phase 2 Handoff

## 1. Scope

- Owner: TV5 integration hardening.
- Branch: `phase2/tv5-integration-hardening`.
- Base: `47bf36300a739b09d343ea5b925feef31f5fd501` (`Merge pull request #22 from qhuynguyen0812-cyber/phase2/tv2-final-hardening`).
- `origin/phase-2/tv5` at `f24ca560ca7d18e6ed0264eb7bb1bc346f629e32` was inspected as reference only. It was not merged, cherry-picked, or copied wholesale.
- Integration consumers: canonical application state, FastAPI state/configuration endpoints, EDA UI, clustering UI, workflow/session state, and HTTP regression coverage.

## 2. State dependency contract

`outlier_strategy` supports only `iqr_clip` and `keep`. An effective strategy change invalidates `processed_df`, `scaled_matrix`, `preprocessing_signature`, `eda_summary`, K analysis/selection, clustering/profile metadata, results, and export payload. It preserves the validated raw dataset, dataset signature, and solver preferences.

`solver_preferences` supports only `max_iter` and `tol`. An effective preference change invalidates model, labels, cluster profiles, run metadata, results, and export payload. It preserves raw and preprocessed data, signatures, EDA, K metrics, recommendation, selected K, and outlier strategy.

Equal effective configuration updates are idempotent and preserve valid descendants.

## 3. Atomicity contract

- Configuration is completely validated before mutation.
- Preprocessing computes successfully before any state mutation.
- Strategy and all preprocessing artifacts are committed together through `set_preprocessed_data`.
- Invalid strategy/configuration and failed computation preserve the prior valid workflow.
- The preprocess endpoint intentionally recomputes and recommits preprocessing even when the requested strategy is unchanged; the direct configuration setters remain idempotent.

## 4. Outlier strategy transport

- Default/UI default: `iqr_clip`.
- Supported alternative: `keep`.
- `POST /api/preprocess` accepts a JSON object containing `outlier_strategy`; an absent body remains backward compatible with `iqr_clip`.
- Unsupported, unknown, and malformed configuration returns HTTP 422.
- `/api/state`, the EDA payload, and the selector expose/synchronize the effective strategy.

## 5. EDA semantics

- Payload fields include `outlier_strategy`, `iqr_applied`, neutral `processed_max`, and `pct_changed`.
- Under `keep`, `iqr_applied` is false, compatibility `pct_clipped` is zero, IQR bounds are absent from preprocessing output, and UI labels explicitly state that clipping was not applied and outliers were preserved.
- Under `iqr_clip`, labels describe before/after IQR clipping and bounds.
- `missing_count` is computed from actual raw RFM cells.
- Zero detected outliers remain zero; no `117` or `720` fallback is used in the TV5 JavaScript or templates.

## 6. Solver preferences

- Editable keys: `max_iter`, `tol` only.
- Partial POST updates merge with existing overrides.
- Defaults remain `max_iter=300` and `tol=0.0001`; fixed solver values remain `init=k-means++`, `n_init=10`, and `random_state=42`.
- `max_iter` must be a non-boolean integer greater than or equal to 1.
- `tol` must be a non-boolean, positive, finite number.
- Unknown keys, booleans, fractional `max_iter`, non-finite tolerance, zero, and negative values return HTTP 422 without mutation.
- The UI displays effective defaults, supports only the two allowed controls, and requires an explicit clustering rerun after an effective change.

## 7. Canonical keep evidence

Observed through the HTTP end-to-end workflow on `data/sample_customers.csv`, K=3:

- Inertia: `882.5146` (serialized to four decimals).
- Silhouette: `0.4502` (serialized to four decimals).
- Iterations: `11`.

## 8. Regression verification

- Baseline before edits: `159 passed, 2 warnings in 22.29s`.
- Targeted state/web tests: `37 passed, 2 warnings in 31.67s`.
- TV1-TV4/TV6 seam suite: `82 passed, 2 warnings in 30.29s`.
- Full suite: `178 passed, 2 warnings in 70.97s`.
- Collection: `178 tests collected in 3.52s`.
- `python -m compileall -q src web components tests`: passed.
- `python -m pip check`: `No broken requirements found.`
- `node --check web/static/js/eda.js`: passed.
- `node --check web/static/js/clustering.js`: passed.
- `git diff --check`: passed; Git emitted only line-ending conversion notices.

## 9. Known warnings

- Existing `StarletteDeprecationWarning`: Starlette TestClient's `httpx` integration is deprecated in favor of `httpx2`.
- Environment-specific joblib warning: physical core count could not be detected (`0 physical cores`), so joblib used logical cores. This warning appeared in baseline and verification and did not affect deterministic results.

## 10. Contract deviation audit

- CustomerID added to ML: NO
- missing strategy changed from median: NO
- default outlier changed from iqr_clip: NO
- keep removed/bypassed: NO
- StandardScaler replaced: NO
- TV3 solver defaults changed: NO
- K recommendation logic changed: NO
- TV4 profiling replaced: NO
- business interpretation duplicated: NO
- TV6 export contract changed: NO
- existing tests deleted/weakened: NO
- production metrics hard-coded: NO
- raw missing_count hard-coded: NO
- demo fallback 117 retained: NO
- catch-all Exception added to normal validation paths: NO

`src/preprocessing.py`, `src/clustering.py`, `src/profiling.py`, `src/validation.py`, and `components/results_export.py` were not modified.

CONTRACT_DEVIATIONS = 0
