# TV6 Phase 2 Academic Demo Checklist

## Source release prerequisites

- [x] Integrated TV1-TV5 source contracts present
- [x] Default `iqr_clip` and Phase 2 `keep` supported end to end
- [x] Editable solver fields limited to `max_iter` and `tol`
- [x] Explicit K confirmation required before clustering
- [x] Current Results and deterministic six-column Export available only after a valid fit
- [x] Windows Python 3.11 release CI configured
- [x] Final source gates rerun and recorded in TV6 release evidence

## Demo sequence

1. Launch the FastAPI app.
2. Load the canonical sample dataset.
3. Explain raw Recency, Frequency, and Monetary; CustomerID is identity only.
4. Show data quality and allowed missing values plus downstream median imputation.
5. Run default `iqr_clip` preprocessing.
6. Show strategy-aware EDA and before/after outlier handling.
7. Run K analysis.
8. Explain Elbow/inertia and Silhouette evidence.
9. Explicitly confirm K rather than accepting an automatic production choice.
10. Run clustering.
11. Explain profile statistics, deterministic segment names, and evidence-limited interpretation.
12. Show customer Results.
13. Export CSV and verify six columns, 720 customers, raw RFM, current Cluster, and SegmentName.
14. Rerun preprocessing with `keep`.
15. Show `iqr_applied=false`, preserved outliers, and different K=3 metrics (inertia about 882.5146, silhouette about 0.4502, 11 iterations).
16. Set custom `max_iter=400` and `tol=0.0002`.
17. Show Results and Export become unavailable while dataset, preprocessing, K analysis, and selected K remain.
18. Rerun clustering.
19. Verify Results metadata reports the effective solver values and Export is available again.
20. Optionally rerun with K=5 and show five profiles/five exported clusters.

## Presenter checks

- [ ] App launches successfully in the presentation environment
- [ ] CDN-backed frontend assets load on the presentation network
- [ ] Default workflow metrics match evidence within deterministic tolerance
- [ ] `keep` workflow metrics match evidence within deterministic tolerance
- [ ] Solver-change stale-output behavior is demonstrated
- [ ] Export opens correctly and has no index column
- [ ] No claim suggests CustomerID is an ML feature
- [ ] No claim turns interpretation into unsupported prediction or causality
- [ ] Backup local screenshots/video prepared if network availability is uncertain

## Release versus submission status

`SOURCE RELEASE READY` may be marked PASS when full tests, collection, compileall, pip check, diff check, evidence, and contract audit pass.

`FINAL SUBMISSION READY` requires separate verification of non-source course artifacts:

- [ ] Final slide deck exists and has been reviewed
- [ ] Member contribution/evaluation document exists and has been reviewed
- [ ] Required final archive/package exists and opens correctly
- [ ] Demo recording or other required demo artifact exists and has been reviewed
- [ ] Submission naming, size, and upload requirements have been checked

Until every applicable item is independently verified: `FINAL SUBMISSION READY = NOT VERIFIED`.
