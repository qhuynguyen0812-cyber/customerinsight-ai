# TV6 Phase 1 contract and integration evidence

Package authority: `CustomerInsight_AI_Implementation_Ready_Package_v1.1_TeamExecution`, version `1.1-IR-TEAM`.

## Canonical integration seam

TV5's `AppState`, obtained through `components.states.get_app_state()`, is the production authority. The Results page consumes `state.results`, `state.cluster_profiles`, and `state.run_metadata`; all three must exist and pass their TV6 validators before tables, metadata, or a download are exposed. It does not require a parallel `results_valid` flag.

Flat `results_valid`, `customer_results`, `cluster_profiles`, and `run_metadata` keys remain only as an explicit compatibility adapter when no canonical `APP_STATE_KEY` exists. If canonical and legacy state coexist, canonical state always wins.

## TV4 to TV6 handoff

`src.profiling.run_clustering_workflow()` retains the production computation path:

- `processed_df` and `scaled_matrix` drive K-Means and processed-scale business profiles.
- Current labels and profile `SegmentName` values form assignments keyed by `CustomerID`.
- `components.results_export.build_customer_results()` joins those assignments one-to-one onto canonical `state.raw_df`.
- The join preserves raw customer order and raw `Recency`, `Frequency`, and `Monetary`, including raw missing values allowed by TV1. TV6 never imputes or clips export values.
- Model, labels, profiles, run metadata, and customer results are committed together through `set_clustering_result()` only after all local work succeeds.

The exact ordered customer result columns are `CustomerID`, `Recency`, `Frequency`, `Monetary`, `Cluster`, and `SegmentName`.

## Validation and export

Customer IDs and assignment IDs must be non-null and unique, and their sets must match exactly. Missing, duplicate, stale, unknown, or incomplete assignments raise `ResultContractError`. Profiles require non-null values for every minimum field and one row per cluster. Run metadata requires non-null `k`, `init`, `n_init`, `random_state`, `max_iter`, `tol`, `inertia`, `silhouette`, `iterations`, and `runtime_seconds`; TV6 does not synthesize them.

CSV serialization validates the result again, omits the DataFrame index, uses deterministic LF line endings, and encodes UTF-8 with BOM. `export_payload` is not duplicated in production state; CSV is serialized on demand from current validated results.

TV5 dependency setters invalidate `model`, `labels`, `cluster_profiles`, `run_metadata`, `results`, and `export_payload` after dataset, preprocessing, selected-K, or solver changes. AppTests verify that the Results page then exposes no stale download.

## Canonical 720-row evidence

`tests/test_tv6_integration.py` executes the real `data/sample_customers.csv` path through TV1 validation, canonical raw commit, TV2 preprocessing and commit, TV3 K analysis and selection, TV4 clustering/profiling, TV6 validation, and CSV export.

- Input and processed rows: 720
- Scaled shape: `(720, 3)`
- Recommended and selected K: 3
- Labels, profile count total, customer result rows, and CSV data rows: 720
- Inertia: `611.4205381920901`
- Silhouette: `0.45877917738169266`
- Iterations: 9
- Customer mapping: 720 unique IDs, all segment names non-null
- Result RFM: exact canonical raw match by `CustomerID`
- CSV: UTF-8 BOM, LF, no index, exact six columns

A separate deliberate missing-value/outlier case proves profiles use processed values while customer results preserve the differing raw values.

## Executed technical gates (2026-08-15)

- Cross-TV regression command covering the ten mandated suites plus TV6 integration: `120 passed`.
- `python -m pytest -q -ra`: `120 passed` (one non-failing joblib CPU-detection warning).
- `python -m pytest --collect-only -q`: `120 tests collected`.
- `python -m compileall -q app.py views src components tests`: passed.
- `python -m pip check`: `No broken requirements found.`
- Imports of `components.results_export`, `src.profiling`, and `src.state`: passed.
- `git diff --check`: passed (Git emitted only configured LF-to-CRLF working-copy notices).

The local bundled Python executable was used because `python` is not present on this shell's PATH.

## Remaining formal release actions

Technical Phase 1 gates pass. Commit, push, PR to `develop`, paired TV5 review evidence, and merge remain manual and were not performed by TV6 integration work.
