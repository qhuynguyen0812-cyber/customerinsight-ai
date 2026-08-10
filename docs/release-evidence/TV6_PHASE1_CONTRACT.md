# TV6 Phase 1 contract and integration handoff

Package authority: `CustomerInsight_AI_Implementation_Ready_Package_v1.1_TeamExecution`, version `1.1-IR-TEAM`.

## Scope and requirements

TV6 owns FR-014, FR-015, FR-016, FR-017, NFR-004, NFR-006, and NFR-007. TV6 reviews FR-018 through FR-021 as a consumer and does not own TV5 state semantics.

## TV4 output expected by TV6

- `customer_results`: a pandas DataFrame whose exact ordered columns are `CustomerID`, `Recency`, `Frequency`, `Monetary`, `Cluster`, `SegmentName`; one current row per unique active customer; raw RFM preserved.
- `cluster_profiles`: a pandas DataFrame containing at least `Cluster`, `SegmentName`, `count`, `mean Recency`, `mean Frequency`, `mean Monetary`.
- `run_metadata`: a mapping containing fields actually computed by the current fit. Supported fields are `k`, `init`, `n_init`, `random_state`, `max_iter`, `tol`, `inertia`, `silhouette`, `iterations`, and `runtime_seconds`. Missing fields remain absent; TV6 does not invent values.

TV4 is not implemented on the kickoff baseline. TV6 therefore validates and consumes these outputs but does not recompute a production model, profile, labels, or metadata.

## TV5 state and gating expected by TV6

The Results page currently reads these integration seam names:

- `results_valid`: exactly `True` only when the model, customer results, profiles, metadata, dataset signature, preprocessing signature, selected K, and solver signature are current.
- `customer_results`: current TV4 customer output.
- `cluster_profiles`: current TV4 profile output, when available.
- `run_metadata`: current TV4 run metadata, when available.

TV5 must own creation, invalidation, and atomic commit of these state values. Changing dataset, preprocessing, K range/selection, or solver configuration must make `results_valid` false and remove/replace stale derived outputs before a Results render. TV6 never writes these state keys.

TV5 is not implemented on the kickoff baseline. FR-018 through FR-021 review and a full canonical AppTest remain blocked until its real branch is merged. If TV5 chooses different public key names, it must provide a stable accessor or coordinate the small adapter change in `views/5_Ket_qua.py`; TV6 will not create a second state model.

## Export contract

`build_customer_results` joins a separate active canonical raw table to current `CustomerID`, `Cluster`, `SegmentName` assignments with a one-to-one merge, preserves raw row order and RFM, and rejects missing, duplicate, stale, or unknown mappings. `customer_results_to_csv_bytes` accepts only a valid current customer table. Output uses the exact six business columns, no DataFrame index, LF line endings, and UTF-8 with BOM. The caller must gate access with TV5's current-results signal. Invalid or incomplete payloads raise `ResultContractError`; the UI shows an error and exposes no download.

## Test entry points

- Pure result/export contract: `tests/test_tv6_results.py`
- Streamlit Results and Algorithm AppTests: `tests/test_app_render.py`
- Full canonical flow: pending the real TV1–TV5 integration APIs; do not substitute fixtures for release evidence.

## AppTest inventory

- Results safely gated before prerequisites.
- Results mapping and download render for a valid current handoff.
- Invalid payload gives a user-facing error without export.
- Algorithm page and educational chart render.
- Educational interaction does not create production result state.

## Upstream consumer actions

1. TV5 confirms or adapts the four read-only state seam names above and proves invalidation/current-signature behavior.
2. TV4 supplies actual customer results, profiles, and run metadata from its atomic production fit.
3. After integration, run the canonical 720-row workflow and extend AppTest to exercise the real Data-to-Export path; record only computed metrics.
4. TV5 reviews this TV6 diff and test evidence before merge.
