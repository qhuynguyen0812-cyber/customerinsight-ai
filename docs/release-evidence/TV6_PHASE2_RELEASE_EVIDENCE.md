# TV6 Phase 2 release evidence

Observed 2026-08-23 (Asia/Bangkok). This document reports only executed checks.

## 1–4. Baseline and environment

- Baseline SHA: `62c16cd` (`origin/main`, `origin/develop`, and TV6 branch before this work).
- TV6 working branch: `phase2/tv6-release-qa`; verified implementation commit `707b1d2`
  (release-evidence documentation is committed separately after the observed checks).
- Integrated develop SHA at final gate: `62c16cd`. Phase 2 owner branches were not integrated.
- Available clean runtime: Python `3.12.13`. No Python 3.11 interpreter was installed, so the
  required clean Python 3.11 gate is BLOCKED. `.venv-clean` is excluded from Git.

## 5–10. Executed technical verification

Commands and observed results:

```text
git fetch --all --prune                         PASS
.venv-clean\Scripts\python.exe -m pytest -q -ra
                                                  107 passed, 2 warnings
.venv-clean\Scripts\python.exe -m pytest --collect-only -q
                                                  107 tests collected, 1 warning
.venv-clean\Scripts\python.exe -m compileall -q web src components tests
                                                  PASS (exit 0, no output)
.venv-clean\Scripts\python.exe -m pip check      No broken requirements found.
git diff --check                                 PASS (line-ending notices only)
```

Warnings were Starlette's TestClient/httpx deprecation notice and joblib's physical-core
detection fallback. Key installed versions included FastAPI 0.141.1, Starlette 1.6.0,
httpx 0.28.1, pandas 3.0.5, NumPy 2.4.6, scikit-learn 1.8.0, and pytest 9.1.1.

## 11–15. Scientific and configuration evidence

- Canonical K=3: PASS. HTTP workflow observed 720 rows, inertia `611.4205`, silhouette
  `0.4588`, and 9 iterations. Existing strict domain tests retain full-precision tolerances.
- `outlier=keep`: BLOCKED BY TV2/TV5. `src/preprocessing.py` rejects every non-`iqr_clip`
  strategy and the API has no preprocessing configuration transport.
- `max_iter`: BLOCKED BY TV5 (TV4 domain support exists). The K-Means core accepts overrides,
  but no FastAPI/UI endpoint stores solver preferences.
- `tol`: BLOCKED BY TV5 for the same transport/state reason.
- K=5: PASS at HTTP level. Five profiles and five exported cluster values were observed;
  counts total 720 and raw RFM/CustomerID mapping round-trips exactly.

## 16–18. Freshness matrices

| Change | Derived state | Results | Export | Evidence |
|---|---|---|---|---|
| New dataset | PASS invalidated | PASS blocked | PASS blocked | `test_new_dataset_invalidates_old_results_and_export` |
| Re-run preprocessing | PASS K/model cleared | PASS blocked | PASS blocked | `test_preprocessing_k_analysis_and_selected_k_changes_block_stale_outputs` |
| K range change | PASS selection/model cleared | PASS blocked | PASS blocked | same test |
| Selected K change | PASS model/profile cleared | PASS blocked | PASS blocked | same test |
| `max_iter` change | BLOCKED: no HTTP transport | BLOCKED | BLOCKED | TV5 dependency |
| `tol` change | BLOCKED: no HTTP transport | BLOCKED | BLOCKED | TV5 dependency |

Export is generated on demand from current validated `state.results`; no duplicate persistent
CSV payload is used in production.

## 19. Failure paths

| Failure | HTTP/state result |
|---|---|
| Missing column, duplicate ID, nonnumeric, negative, infinity, malformed shape | 422; prior valid results/export unchanged |
| Invalid K range or selected K | 422; prior valid results/export unchanged |
| Premature results/export | 422; Results page redirects to workflow prerequisite |
| Invalid preprocessing strategy | Domain rejection covered; HTTP transport not integrated |
| Invalid solver settings | Domain rejection covered; HTTP transport not integrated |
| Injected clustering/profile failure | Existing atomic domain setters covered; dedicated HTTP fault injection not added |

## 20–21. Isolation and missing-value JSON

- Session isolation: PASS with two independent TestClient cookie jars. A complete run in A is
  invisible to B; loading B leaves A's results and export intact.
- Missing RFM JSON: PASS. An upload with three allowed missing RFM cells returns HTTP 200,
  serializes them as JSON `null`, reports `missing_count = 3`, and can be preprocessed.

## 22. Browser QA

Automated in-app browser checks completed the canonical Overview → Sample → Data → EDA →
K analysis → Confirm K → Clustering → Results → Export flow. Canonical metrics and all 720
Customer Explorer rows rendered. Overview and Results had no document-level horizontal
overflow at widths 1920, 1440, 1366, and 1280. Current CSV download fired successfully.

No JavaScript errors were observed, but the console emitted Tailwind CDN production warnings.
Invalid-upload, missing-RFM, K=5, `keep`, custom solver, reduced-motion, and rerun-after-
invalidation browser flows were not all visually exercised. Therefore P2 browser QA is
BLOCKED pending those manual checks and owner integration; it is not claimed as full PASS.

## 23. Security and NFR audit

- No API keys, passwords, tokens, unsafe `eval`, unsafe Python `exec`, uploaded-content shell
  execution, or user-controlled filesystem paths were found in the scoped source.
- Customer IDs and segment names inserted by Results JavaScript are HTML-escaped.
- CSV formula neutralization is not part of the locked six-column/raw-value contract; consumers
  should import exported CSV as data and avoid executing spreadsheet formulas.
- No benchmark supports production/enterprise/real-time/millions/high-availability claims.
  The project is documented as a local academic application.
- Tailwind, Google Fonts, and Plotly use external CDNs; full offline support is not claimed.

## 24–26. Limitations, blockers, and final state

Known limitations/blockers:

- TV2/TV5: `outlier=keep` implementation and API/UI transport are absent from integrated develop.
- TV5: solver preference API/UI transport for `max_iter` and `tol` is absent.
- TV1 and TV4 Phase 2 commits exist only on remote owner branches and were not merged.
- Clean Python 3.11 verification cannot run because the interpreter is unavailable locally.
- Browser QA is partial and CDN-dependent; final manual checks remain.
- No final slide deck, member evaluation, submission archive, or retained screenshots are present.

Final observed state:

```text
TV6 SCOPE = BLOCKED
PHASE 2 = BLOCKED
SOURCE RELEASE READY = BLOCKED
SUBMISSION READY = BLOCKED
```

## Phase 2 release matrix

| ID | Requirement | Owner | Test/evidence | Status | Notes |
|---|---|---|---|---|---|
| P2-G01 | `outlier=keep` | TV2/TV5 | source/API audit | BLOCKED | not integrated |
| P2-G02 | `max_iter`/`tol` | TV4/TV5 | domain tests + API audit | BLOCKED | transport absent |
| P2-G03 | legacy evidence cleanup | TV6 | README/spec/history edits | PASS | v1.2 current |
| P2-G04 | state invalidation | TV5/TV6 | HTTP freshness tests | PASS | integrated cases pass |
| P2-G05 | stale results prevention | TV6 | HTTP freshness tests | PASS | 422/redirect after invalidation |
| P2-G06 | stale export prevention | TV6 | HTTP freshness tests | PASS | 422 after invalidation |
| P2-G07 | failure atomicity | owners/TV6 | HTTP invalid-input tests | PASS | available paths pass |
| P2-G08 | missing-value JSON | TV5/TV6 | missing upload HTTP test | PASS | null + count 3 |
| P2-G09 | session isolation | TV5/TV6 | two-client HTTP test | PASS | both directions |
| P2-G10 | K=5 | TV4/TV6 | dynamic export HTTP test | PASS | five profiles/clusters |
| P2-G11 | clean environment | TV6 | Python 3.12 clean run | BLOCKED | Python 3.11 unavailable |
| P2-G12 | browser QA | TV6 | in-app browser run | BLOCKED | partial; CDN warning |
| P2-G13 | security/NFR | TV6 | scoped scan + XSS fix | PASS | limitations documented |
| P2-G14 | release evidence | TV6 | this document | PASS | observed evidence only |
| P2-G15 | academic/demo checklist | TV6/submission owner | companion checklist | BLOCKED | deck/member artifacts absent |
