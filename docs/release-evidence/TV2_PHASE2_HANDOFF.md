# TV2 Phase 2 Handoff

## 1. Scope

- Owner: TV2.
- Branch: `phase2/tv2-final-hardening`.
- Integration base: `develop`; observed base SHA: `e2adb28`.
- Requirements and gate: FR-005, FR-006, FR-007, FR-008, and P2-G01.
- Input: TV1's validated canonical `CustomerID`, `Recency`, `Frequency`, and `Monetary` dataset.
- Consumers: TV3 clustering analysis, TV5 web/API/state integration, and TV6 release verification.

## 2. Scientific preprocessing contract

- Missing RFM values use per-feature median imputation.
- The default outlier strategy remains `iqr_clip`, using the existing Tukey IQR clipping implementation.
- The Phase 2 `keep` path median-imputes but does not clip outlier values.
- Scaling uses `StandardScaler`.
- Scaling and ML input contain exactly `Recency`, `Frequency`, and `Monetary`.
- `CustomerID` is identity only and is preserved; it is never passed to the scaler or ML pipeline.

## 3. P2-G01 evidence

The hardened tests prove that `outlier_strategy="keep"`:

- preserves actual high outlier values without clipping;
- returns `iqr_bounds == {}`;
- still performs correct per-feature median imputation;
- preserves every row and exact customer identity, including text such as `"001"`;
- produces a finite N x 3 RFM-only scaled output;
- is deterministic for equivalent inputs; and
- has a preprocessing signature distinct from `iqr_clip`, while the IQR path supplies non-empty bounds and reduces the same high values.

## 4. Regression coverage

All Phase 1 regression coverage remains in place:

- canonical RFM features;
- per-feature median imputation and CustomerID preservation;
- exact IQR bounds and clipping without row removal;
- finite, deterministic, RFM-only StandardScaler output;
- invalid missing and outlier strategy rejection;
- all-missing feature and infinity rejection;
- canonical TV1 720-row to 720 x 3 handoff;
- downstream state invalidation; and
- failed preprocessing preserving previous valid state.

No existing test was deleted or weakened. The weak Phase 2 smoke test was replaced with four stronger P2-G01 contract tests.

## 5. Verification

Actual observed results on this branch:

- `.venv-clean\Scripts\python.exe -m pytest tests/test_preprocessing.py -q -ra`: **18 passed in 9.18s**.
- `.venv-clean\Scripts\python.exe -m pytest tests/test_validation.py tests/test_clustering.py tests/test_profiling.py tests/test_state.py -q -ra`: **49 passed, 1 warning in 6.19s**.
- `.venv-clean\Scripts\python.exe -m pytest -q -ra`: **159 passed, 2 warnings in 37.60s**.
- `.venv-clean\Scripts\python.exe -m pytest --collect-only -q`: **159 tests collected in 3.92s**.
- `.venv-clean\Scripts\python.exe -m compileall -q src web components tests`: **PASS**.
- `.venv-clean\Scripts\python.exe -m pip check`: **No broken requirements found**.
- `git diff --check`: **PASS**; Git emitted only an LF-to-CRLF working-copy notice for `tests/test_preprocessing.py`.

Warnings observed:

- Existing `StarletteDeprecationWarning` for the Starlette/httpx TestClient compatibility path.
- Environment-specific joblib warning because physical CPU cores could not be detected; joblib used logical cores.

## 6. Contract deviation audit

- CustomerID added to ML: NO
- median strategy changed: NO
- default iqr_clip changed: NO
- keep removed: NO
- StandardScaler replaced: NO
- K analysis changed: NO
- KMeans solver changed: NO
- profiling changed: NO
- tests deleted: NO
- assertions weakened: NO
- production metrics hard-coded: NO

CONTRACT_DEVIATIONS = 0

## 7. Known integration dependencies

- TV5 owns UI/API/state transport of the selected outlier strategy.
- TV5 must invalidate downstream artifacts whenever preprocessing configuration changes.
- TV6 must rerun the complete `keep` workflow on the final integrated release commit.
- EDA seam: `web/app.py` does not transport the chosen outlier strategy in `eda_data`, while `web/templates/eda.html` and `web/static/js/eda.js` unconditionally describe processed values as IQR-clipped. TV5 should make those labels and before/after semantics strategy-aware for `keep`.
- Raw RFM `missing_count` is not hard-coded in the backend; it is computed from `raw_df` both before and after preprocessing. Any UI fallback/default behavior remains a TV5 web/state presentation concern.
