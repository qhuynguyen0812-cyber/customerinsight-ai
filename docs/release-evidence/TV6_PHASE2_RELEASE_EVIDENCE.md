# TV6 Phase 2 Final Release Evidence

## 1. Final integrated baseline

- Branch: `phase2/tv6-final-release-qa`
- Base: `9711a6e` (`Merge pull request #23 from qhuynguyen0812-cyber/phase2/tv5-integration-hardening`)
- Pre-change tree: clean
- Local runtime: Python 3.12.13 (`.venv-clean`)
- Release CI: Windows with Python 3.11
- Pre-change baseline: 178 passed, 2 warnings in 65.20s
- Final test count: 197 passed, 2 warnings in 105.20s

## 2. Integrated owner matrix

| Owner | Status | Integrated contract evidence |
| --- | --- | --- |
| TV1 validation | PASS | Canonical columns, textual/unique CustomerID, invalid-input rejection, missing-RFM acceptance, failed-upload atomicity |
| TV2 preprocessing | PASS | Median imputation, default `iqr_clip`, Phase 2 `keep`, RFM-only scaling |
| TV3 K analysis/solver | PASS | Silhouette recommendation, explicit K confirmation, deterministic defaults, `max_iter`/`tol` overrides |
| TV4 clustering/profile | PASS | K/label/profile agreement, deterministic profiles, complete typed run metadata, atomic publication |
| TV5 workflow/state | PASS | Configuration transport, dependency-scoped invalidation, atomic invalid configuration, session isolation |

## 3. Canonical `iqr_clip` workflow

The HTTP release workflow loads `data/sample_customers.csv`, preprocesses, analyzes K, explicitly selects K=3, clusters, reads Results, and exports CSV.

- Rows: 720
- Strategy: `iqr_clip`; `iqr_applied=true`
- Selected K: 3
- Inertia: approximately 611.4205381920901 (API serialization: 611.4205)
- Silhouette: approximately 0.45877917738169266 (API serialization: 0.4588)
- Iterations: 9
- Profiles: 3; profile counts sum to 720
- Export: 720 rows and complete raw-RFM mapping

Evidence: `test_canonical_phase2_workflows_publish_current_results_and_export[iqr_clip-...]`.

## 4. Canonical `keep` workflow

- Strategy: `keep`; preprocessing completes with `iqr_applied=false`
- No clipping claim: `pct_clipped=0.0`; outliers are retained while missing values are still imputed
- Selected K: 3
- Inertia: approximately 882.5145827792722 (API serialization: 882.5146)
- Silhouette: approximately 0.4502395249927606 (API serialization: 0.4502)
- Iterations: 11
- Export: 720 rows; CustomerID one-to-one; raw RFM exact; Cluster and SegmentName complete
- Repeated export bytes are identical

Evidence: `test_canonical_phase2_workflows_publish_current_results_and_export[keep-...]`.

## 5. Solver override evidence

`POST /api/solver-preferences` with `max_iter=400` and `tol=0.0002` preserves the dataset, preprocessing, K metrics, recommendation, and selected K while clearing model, labels, profiles, Results, and Export. Both output endpoints return 422 until clustering is rerun.

After rerun, effective metadata reports K=3, `init=k-means++`, `n_init=10`, `random_state=42`, `max_iter=400`, and `tol=0.0002`, with finite positive inertia/silhouette, valid iterations, and non-null runtime.

Evidence: `test_solver_override_invalidates_only_fit_outputs_then_reaches_model_metadata`.

## 6. Freshness matrix

| Change | Invalidated | Results / Export | Evidence |
| --- | --- | --- | --- |
| New dataset | preprocessing, K analysis/selection, fit/profile/output | 422 / 422 | `test_new_dataset_invalidates_old_results_and_export` |
| Preprocess rerun | K analysis/selection, fit/profile/output | 422 / 422 | `test_preprocessing_k_analysis_and_selected_k_changes_block_stale_outputs` |
| Outlier strategy change | preprocessing descendants through output | 422 / 422 until full K/fit rerun | `test_strategy_change_preserves_inputs_and_invalidates_all_preprocessing_descendants` |
| K analysis rerun | selected K and fit/profile/output | 422 / 422 | `test_preprocessing_k_analysis_and_selected_k_changes_block_stale_outputs` |
| Selected K change | fit/profile/output | 422 / 422 | same test |
| Solver preference change | fit/profile/output only | 422 / 422 until clustering rerun | `test_solver_override_invalidates_only_fit_outputs_then_reaches_model_metadata` |

The Results page redirects to the clustering prerequisite whenever output is stale.

## 7. Failure atomicity

- Invalid uploads: malformed schema, duplicate CustomerID, nonnumeric/negative/infinite RFM all return 422 and preserve prior Results and exact Export bytes.
- Invalid K range and invalid selected K return 422 without replacing a valid run.
- Invalid outlier strategy and malformed preprocessing JSON return 422 while preserving strategy, preprocessing signature, K, Results, and Export bytes.
- Invalid solver values cover boolean/fractional/nonpositive `max_iter`; boolean/nonpositive/NaN/positive infinity/negative infinity `tol`; and unknown keys. Each returns 422 and preserves solver preferences, selected K, Results, and Export bytes.

Evidence: `test_invalid_upload_variants_never_partially_replace_a_valid_run`, `test_invalid_k_requests_are_atomic_and_do_not_expose_partial_state`, `test_invalid_outlier_configuration_is_release_atomic`, and `test_invalid_solver_configuration_is_release_atomic`.

## 8. Session isolation

Two independent TestClient sessions prove no cross-session leakage of dataset state, `outlier_strategy`, solver preferences, selected K, Results, or Export eligibility. Client A completes `keep` with custom solver settings; client B begins empty/default, runs independently, and does not alter A.

Evidence: `test_phase2_configuration_and_outputs_are_session_isolated` and `test_sessions_are_isolated_in_both_directions`.

## 9. Missing-value JSON

An upload containing three missing RFM cells returns HTTP 200, reports the actual count 3, and serializes preview/chart missing values as JSON `null`, not NaN/Infinity. Default preprocessing succeeds and retains the actual missing count while median-imputing downstream.

Evidence: `test_missing_rfm_upload_is_valid_json_and_can_be_preprocessed`.

## 10. Dynamic K=5

The complete HTTP workflow explicitly selects K=5 and produces model metadata K=5, five profile rows, five unique exported clusters, profile counts totaling 720, and 720 customer results with exact raw RFM. Repeated export is deterministic.

Evidence: `test_dynamic_k5_export_is_current_complete_and_deterministic`.

## 11. Results/export contract

The exact ordered schema is `CustomerID, Recency, Frequency, Monetary, Cluster, SegmentName`. Results retain active raw row order and raw RFM, require unique/non-null CustomerID, reject unknown, duplicate, stale, or incomplete assignments, and filter metadata to required supplied values without inventing fields. CSV is deterministic UTF-8-SIG with BOM, LF endings, no index, one row per active customer, and current assignments only.

Evidence: `tests/test_tv6_results.py` plus both canonical workflow tests and dynamic K=5.

## 12. Security/NFR

- Repository scan found no embedded API key, password, or secret assignment in source/tests.
- No `eval`, `exec`, `os.system`, subprocess, or shell execution path was found in application source.
- `results.js` escapes dynamic CustomerID, segment/cluster labels, names, insights/descriptions before HTML insertion; a regression test protects these sinks.
- Numeric chart/model values remain numeric rather than unnecessarily HTML-escaped.
- The results UI no longer fabricates a 720-row fallback.
- Frontend CDN dependencies remain a network availability dependency; acceptable for local academic/demo scope, but not an offline or enterprise-readiness claim.
- No arbitrary external input is claimed safe merely because current profile text is internally generated.

## 13. Environment / CI

`.github/workflows/python-release.yml` uses `windows-latest` and Python 3.11, installs requirements, and runs full pytest, collection, compileall over `web src components tests`, and pip check. Local verification uses Python 3.12.13 because that is the available clean repository environment.

- Targeted TV6: 44 passed, 2 warnings in 67.65s
- Integration seams: 94 passed, 2 warnings in 36.21s
- Full suite: 197 passed, 2 warnings in 105.20s
- Collection: 197 tests collected in 3.66s
- Compileall: PASS (exit 0)
- Pip check: PASS (`No broken requirements found.`)
- JavaScript syntax: PASS for `web/static/js/results.js`
- `git diff --check`: PASS; only informational LF-to-CRLF working-copy notices

`git diff --check` was not added to CI because the required CI already matches the release contract and Windows line-ending notices could create avoidable churn.

## 14. Known warnings

- Starlette deprecates the current TestClient/httpx compatibility path in favor of `httpx2`.
- joblib/loky could not detect physical cores in this environment and used logical cores. This does not affect deterministic results.

## 15. Source release decision

All TV6 source gates pass. Source readiness is distinct from final submission readiness. No slide deck, member evaluation, packaged archive, or independently recorded demo artifact was found in the repository, so `SUBMISSION READY` cannot be marked PASS from source evidence alone.

- `TV6 SCOPE = PASS`
- `PHASE 2 SOURCE = PASS`
- `SOURCE RELEASE READY = PASS`
- `SUBMISSION READY = NOT VERIFIED`

## 16. Contract deviation audit

- CustomerID used as ML feature: NO
- median imputation changed: NO
- default outlier changed: NO
- `keep` removed: NO
- StandardScaler changed: NO
- solver defaults changed: NO
- automatic K selection added: NO
- profiling contract replaced: NO
- business interpretation duplicated: NO
- raw RFM export changed: NO
- six-column export schema changed: NO
- stale results allowed: NO
- stale export allowed: NO
- hard-coded production metrics added: NO
- hard-coded demo row counts added: NO
- existing tests weakened/deleted: NO

`CONTRACT_DEVIATIONS = 0`
