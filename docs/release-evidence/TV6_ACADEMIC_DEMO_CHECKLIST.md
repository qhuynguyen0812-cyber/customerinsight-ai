# Phase 2 academic deck and demo checklist

This checklist prevents slide/demo claims from getting ahead of the verified source.
No slide deck is stored in this repository, so deck edits and member evaluation remain
submission-owner actions.

## Deck content

- [ ] Artificial Intelligence, Machine Learning, and Unsupervised Learning context
- [ ] Customer segmentation and RFM definitions: Recency, Frequency, Monetary
- [ ] CustomerID is identity/mapping only and is excluded from K-Means features
- [ ] Missing values use per-feature median imputation
- [ ] Default outlier handling is IQR clipping; Phase 2 `keep` is shown only after integration
- [ ] StandardScaler, Euclidean distance, centroid, assignment, centroid update, and convergence
- [ ] K-Means++, Lloyd algorithm, inertia/WCSS, Elbow, and Silhouette
- [ ] Recommended K does not replace explicit user confirmation
- [ ] Cluster profiles, cautious business interpretation, benefits, and limitations
- [ ] Reproducibility, testing evidence, demo, conclusion, member evaluation, and source submission

TV6-provided content is in `TV6_PHASE2_RELEASE_EVIDENCE.md`: testing, limitations,
release readiness, and the conclusion that Phase 2 is currently blocked.

## Demo rehearsal order

1. Create/activate Python 3.11 environment and install `requirements.txt`.
2. Run `python -m uvicorn web.app:app --host 127.0.0.1 --port 8000`.
3. Open Overview and load the canonical sample.
4. Explain Data Quality, then run preprocessing and inspect EDA.
5. Run K analysis; explain Elbow and Silhouette; explicitly confirm K.
6. Run clustering and inspect profiles and metadata.
7. Use Results Customer Explorer and export the current CSV.
8. After owner integration, optionally demonstrate `outlier=keep` and custom `max_iter`/`tol`.
9. If time permits, change an upstream input and show that Results/export are blocked.

## Classroom contingency

- Canonical input: `data/sample_customers.csv`.
- Launch and verification commands are in `README.md`.
- The app currently loads Tailwind, Google Fonts, and Plotly from CDNs. Internet failure can
  reduce styling or remove charts/fonts; full offline frontend support is not claimed.
- Before submission, retain a known-good exported CSV and screenshots outside source control.
- [ ] Final native slide deck located and updated
- [ ] Member evaluation completed
- [ ] Submission source/archive prepared and opened once for verification
