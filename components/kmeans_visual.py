"""Isolated educational K-Means visualization.

The fixed teaching points never read from or write to production model state.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


TEACHING_POINTS = np.array(
    [
        [1.0, 1.2],
        [1.4, 1.8],
        [2.0, 1.1],
        [6.0, 5.7],
        [6.8, 6.2],
        [7.2, 5.4],
    ],
    dtype=float,
)
INITIAL_CENTROIDS = np.array([[1.0, 1.2], [7.2, 5.4]], dtype=float)


def educational_lloyd_state(step: int) -> tuple[np.ndarray, np.ndarray]:
    """Return labels and centroids for one deterministic teaching iteration."""
    if step not in (1, 2, 3, 4):
        raise ValueError("Educational step must be from 1 to 4.")

    centroids = INITIAL_CENTROIDS.copy()
    distances = np.linalg.norm(TEACHING_POINTS[:, None, :] - centroids[None, :, :], axis=2)
    labels = distances.argmin(axis=1)
    if step >= 3:
        centroids = np.vstack(
            [TEACHING_POINTS[labels == cluster].mean(axis=0) for cluster in range(2)]
        )
    if step == 4:
        distances = np.linalg.norm(
            TEACHING_POINTS[:, None, :] - centroids[None, :, :], axis=2
        )
        labels = distances.argmin(axis=1)
    return labels, centroids


def build_kmeans_education_figure(step: int) -> go.Figure:
    """Build a Plotly teaching figure for the selected Lloyd concept step."""
    labels, centroids = educational_lloyd_state(step)
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=TEACHING_POINTS[:, 0],
            y=TEACHING_POINTS[:, 1],
            mode="markers",
            marker={"size": 13, "color": labels, "colorscale": "Bluered"},
            name="Điểm dữ liệu",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=centroids[:, 0],
            y=centroids[:, 1],
            mode="markers",
            marker={"size": 18, "symbol": "x", "color": "black"},
            name="Centroid",
        )
    )
    figure.update_layout(
        title="Mô phỏng Lloyd độc lập với kết quả phân cụm thật",
        xaxis_title="Đặc trưng đã chuẩn hóa 1",
        yaxis_title="Đặc trưng đã chuẩn hóa 2",
        height=430,
    )
    return figure
