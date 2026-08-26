# TV4 Phase 2 Handoff

## Scope

- TV: TV4
- Branch: `phase2/tv4-clustering-hardening`
- Base: `dc9400096c808be47dee627bb560941f670129d2` (`origin/develop`, verified 2026-08-26 after `git fetch --all --prune`)
- Requirements: FR-011, FR-012, FR-013, Phase 2 clustering/profile hardening
- Input consumers: TV3 `KMeansResult`; TV2 `processed_df` and `scaled_matrix`; TV5 solver-preference state
- Outputs: model, labels, cluster profiles, run metadata, customer results
- Downstream consumers: TV5 and TV6
- Required reviewer: TV3 (approval pending; no reviewer approval is claimed here)

## Contract and implementation evidence

- The workflow consumes `run_kmeans(...)` as a `KMeansResult` through `fit.model`, `fit.labels`, `fit.inertia`, and `fit.iterations`. It neither duplicates fitting nor recomputes inertia.
- A publishable run requires the number of distinct fitted labels and profile rows to equal `selected_k`; profile counts must cover every active customer.
- Undefined/degenerate silhouette is rejected as a domain failure. No `silhouette = 0.0` success fallback remains.
- Run metadata is serialized to explicit JSON-safe Python scalar types and reads solver values from the fitted model.
- Business profiles use processed business RFM values. TV6 customer results preserve active raw RFM and map each `CustomerID` one-to-one.
- Fit, profile, and post-profile mapping failures occur before the single state commit and preserve every prior model, labels, profile, metadata, results, and export artifact by identity.
- A successful rerun uses the existing state dependency contract to invalidate stale `export_payload`.
- Segment names are deterministic from relative RFM statistics, independent of numeric cluster meaning, and contain no unsupported promotion, discount, sale-hunter, or churn claim.

## Scientific and dynamic evidence

Canonical sample, default preprocessing, selected K=3:

- rows: 720
- inertia: `611.4205381920901`
- silhouette: `0.45877917738169266`
- iterations: 9
- model clusters: 3
- unique fitted labels: 3
- profile rows: 3
- profile count sum: 720
- mapped customers: 720, unique and in active raw order

Canonical sample, default preprocessing, selected K=5:

- model clusters: 5
- unique fitted labels: 5
- profile rows: 5
- profile count sum: 720
- mapped customers: 720, unique
- metadata K: 5

Non-default solver evidence:

- requested and fitted `max_iter`: 400
- requested and fitted `tol`: 0.0002
- unchanged `init`: `k-means++`
- unchanged `n_init`: 10
- unchanged `random_state`: 42
- metadata reports the fitted values above

## Failure and atomicity evidence

- Controlled `run_kmeans(...)` failure: expected `ValueError`; all six prior artifacts preserved by identity.
- Controlled `compute_cluster_profiles(...)` failure after a successful fit: expected `ValueError`; all six prior artifacts preserved by identity.
- Controlled `build_customer_results(...)` failure after profile generation: expected `ValueError`; all six prior artifacts preserved by identity.
- Simulated selected K=3 fit with two distinct labels: rejected before silhouette/profile publication; all six prior artifacts preserved and no fake metric published.

## UI audit

Zero UI changes were required. The existing clustering page renders profile collections dynamically (including K=5), displays backend K and effective solver/metric values, surfaces backend errors, and renders final scatter state directly under reduced motion.

## Verification

Targeted commands (all run with `.venv-clean\\Scripts\\python.exe` because the repository's `.venv` references a removed interpreter):

| Command | Observed result |
| --- | --- |
| `python -m pytest tests/test_profiling.py -q -ra` | 6 passed |
| `python -m pytest tests/test_tv4_clustering_hardening.py -q -ra` | 9 passed, 1 warning |
| `python -m pytest tests/test_clustering.py -q -ra` | 17 passed, 1 warning |
| `python -m pytest tests/test_tv3_k_hardening.py -q -ra` | 31 passed, 2 warnings |
| `python -m pytest tests/test_web_api.py -q -ra` | 8 passed, 1 warning |
| `python -m pytest tests/test_tv6_release_http.py -q -ra` | 12 passed, 2 warnings |
| `python -m pytest tests/test_tv6_results.py -q -ra` | 13 passed |

Full gates:

| Command | Observed result |
| --- | --- |
| `python -m pytest -q -ra` | 155 passed, 0 skipped, 2 warnings in 23.82s |
| `python -m pytest --collect-only -q` | 155 tests collected; 1 collection warning |
| `python -m compileall -q src web components tests` | PASS |
| `python -m pip check` | No broken requirements found |
| `git diff --check` | PASS (Git emitted an informational LF-to-CRLF working-copy warning) |

Warnings are non-failing environment/dependency notices:

1. joblib/loky could not detect physical cores and used logical cores.
2. Starlette reports that its current `httpx` test-client integration is deprecated in favor of `httpx2`.

Contract deviations: **0**.

## Prepared PR update (do not push in this task)

Suggested title: `phase2(tv4): harden clustering profiles and atomic run contract`

Base: `develop`
Head: `phase2/tv4-clustering-hardening`
Owner: TV4
Reviewer: TV3

Suggested body summary:

- Implements FR-011, FR-012, and FR-013 hardening while preserving the TV3 `KMeansResult` contract.
- Enforces exact selected-K/label/profile consistency and rejects degenerate fits without fabricated silhouette.
- Verifies dynamic K5, complete typed metadata, and actual non-default `max_iter`/`tol` behavior.
- Proves atomic fit/profile/mapping failure and successful-run export invalidation.
- Preserves 720/720 raw-RFM customer mapping and evidence-limited segment naming.
- Makes no UI redesign and no preprocessing, K-analysis, state architecture, or export ownership changes.
- Verification: 155 passed, 0 skipped, 2 warnings; compileall, pip check, and diff check pass; contract deviations: 0.

PR #13 remains on its pre-rebase remote history and was not pushed, force-pushed, updated, merged, or otherwise modified during this task.
