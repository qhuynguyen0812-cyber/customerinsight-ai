(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  let currentState = null;
  let currentKMetrics = [];
  let recommendedK = null;
  let chosenK = null;
  let isConfirmed = false;

  function renderCharts(metrics, targetK) {
    if (!window.Plotly || !metrics || metrics.length === 0) return;

    const kLabels = metrics.map((m) => String(m.k));
    const inertiaValues = metrics.map((m) => m.inertia);
    const silhouetteValues = metrics.map((m) => m.silhouette);

    const activeIndex = metrics.findIndex((m) => m.k === targetK);
    const pointSizes = metrics.map((m, idx) => (idx === activeIndex ? 10 : 5));
    const pointColors = metrics.map((m, idx) => (idx === activeIndex ? "#3525cd" : "#4f46e5"));

    // 1. Elbow Chart
    const elbowTrace = {
      x: kLabels,
      y: inertiaValues,
      type: "scatter",
      mode: "lines+markers",
      line: { color: "#4f46e5", width: 2.5, shape: "spline" },
      marker: { size: pointSizes, color: pointColors },
      fill: "tozeroy",
      fillcolor: "rgba(79, 70, 229, 0.06)",
      name: "Inertia",
      hovertemplate: "<b>K = %{x}</b><br>Inertia: %{y:.4f}<extra></extra>"
    };

    const elbowLayout = {
      margin: { t: 15, r: 15, b: 35, l: 50 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { family: "Inter, sans-serif", size: 11, color: "#464555" },
      xaxis: {
        title: { text: "Số cụm (K)", font: { size: 11, color: "#464555" } },
        gridcolor: "#e5eeff",
        zeroline: false
      },
      yaxis: {
        title: { text: "Inertia", font: { size: 11, color: "#464555" } },
        gridcolor: "#e5eeff",
        zeroline: false
      },
      showlegend: false,
      autosize: true
    };

    Plotly.newPlot("chart-elbow", [elbowTrace], elbowLayout, { responsive: true, displayModeBar: false });

    // 2. Silhouette Chart
    const silColors = metrics.map((m, idx) => (idx === activeIndex ? "#006a61" : "#26a69a"));
    const silSizes = metrics.map((m, idx) => (idx === activeIndex ? 10 : 5));

    // Find max silhouette for annotation
    let maxSil = -Infinity;
    let maxK = metrics[0].k;
    metrics.forEach((m) => {
      if (m.silhouette > maxSil) {
        maxSil = m.silhouette;
        maxK = m.k;
      }
    });

    const silTrace = {
      x: kLabels,
      y: silhouetteValues,
      type: "scatter",
      mode: "lines+markers",
      line: { color: "#006a61", width: 2.5, shape: "spline" },
      marker: { size: silSizes, color: silColors },
      name: "Silhouette",
      hovertemplate: "<b>K = %{x}</b><br>Silhouette: %{y:.4f}<extra></extra>"
    };

    const silLayout = {
      margin: { t: 25, r: 15, b: 35, l: 50 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { family: "Inter, sans-serif", size: 11, color: "#464555" },
      xaxis: {
        title: { text: "Số cụm (K)", font: { size: 11, color: "#464555" } },
        gridcolor: "#e5eeff",
        zeroline: false
      },
      yaxis: {
        title: { text: "Silhouette Score", font: { size: 11, color: "#464555" } },
        gridcolor: "#e5eeff",
        zeroline: false
      },
      annotations: [
        {
          x: String(maxK),
          y: maxSil,
          xref: "x",
          yref: "y",
          text: `Cao nhất · ${maxSil.toFixed(4)}`,
          showarrow: true,
          arrowhead: 2,
          arrowsize: 1,
          arrowwidth: 1.5,
          arrowcolor: "#006a61",
          ax: 0,
          ay: -25,
          font: { family: "Inter, sans-serif", size: 10, color: "#006a61", weight: 700 },
          bgcolor: "rgba(134, 242, 228, 0.4)",
          bordercolor: "#006a61",
          borderwidth: 1,
          borderpad: 4
        }
      ],
      showlegend: false,
      autosize: true
    };

    Plotly.newPlot("chart-silhouette", [silTrace], silLayout, { responsive: true, displayModeBar: false });
  }

  function setChosenK(k) {
    chosenK = k;
    const match = currentKMetrics.find((m) => m.k === k);
    const sil = match ? match.silhouette.toFixed(4) : "—";

    if (!isConfirmed) {
      if (byId("panel-k-value")) byId("panel-k-value").textContent = `K = ${k}`;
      if (byId("panel-sil-score")) byId("panel-sil-score").textContent = sil;
      if (byId("btn-confirm-k")) byId("btn-confirm-k").textContent = `Xác nhận K = ${k}`;

      const desc = byId("panel-desc-text");
      if (desc) {
        if (k === recommendedK) {
          desc.textContent = `K = ${k} đạt Silhouette Score cao nhất (${sil}) trong phạm vi đã đánh giá, cho thấy mức độ phân tách cụm tốt nhất.`;
        } else {
          desc.textContent = `Bạn đang chọn K = ${k} (Silhouette = ${sil}). Đề xuất tự động từ thuật toán là K = ${recommendedK}.`;
        }
      }
    }

    renderTable(currentKMetrics, recommendedK, chosenK);
    renderCharts(currentKMetrics, chosenK);
  }

  function renderTable(metrics, recK, curChosenK) {
    const tbody = byId("candidate-table-body");
    if (!tbody || !metrics || metrics.length === 0) return;

    tbody.innerHTML = metrics
      .map((row) => {
        const isRec = row.k === recK;
        const isSelected = row.k === curChosenK;
        const rowClass = isSelected
          ? "bg-surface-container-high/60 cursor-pointer transition-colors"
          : isRec
          ? "bg-surface-container-low cursor-pointer hover:bg-surface-container transition-colors"
          : "cursor-pointer hover:bg-surface-container-lowest transition-colors";

        const kDisplay = isSelected
          ? `<span class="font-bold text-primary">${row.k}</span>`
          : isRec
          ? `<span class="font-bold text-on-surface">${row.k}</span>`
          : `<span>${row.k}</span>`;

        const silDisplay = isRec
          ? `<span class="font-bold text-secondary">${row.silhouette.toFixed(4)}</span>`
          : `<span>${row.silhouette.toFixed(4)}</span>`;

        const badge = isRec
          ? `<span class="inline-flex items-center gap-xs px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-container font-label-sm text-[10px] uppercase font-bold"><span class="material-symbols-outlined text-[12px]">star</span> Đề xuất</span>`
          : isSelected
          ? `<span class="inline-flex items-center gap-xs px-2 py-0.5 rounded-full bg-primary-container/20 text-primary font-label-sm text-[10px] uppercase font-bold">Đang chọn</span>`
          : `<span class="text-on-surface-variant text-sm">—</span>`;

        return `
          <tr class="${rowClass}" data-k="${row.k}">
            <td class="p-md font-medium">${kDisplay}</td>
            <td class="p-md text-on-surface-variant">${row.inertia.toFixed(4)}</td>
            <td class="p-md">${silDisplay}</td>
            <td class="p-md">${badge}</td>
          </tr>
        `;
      })
      .join("");

    // Attach click listeners to rows
    tbody.querySelectorAll("tr").forEach((tr) => {
      tr.addEventListener("click", () => {
        const kVal = parseInt(tr.getAttribute("data-k"), 10);
        if (kVal) setChosenK(kVal);
      });
    });
  }

  function updateWorkflowProgressUI(completedSteps, totalSteps, percent, nextStep) {
    const bar = byId("workflow-progress-bar");
    const count = byId("workflow-progress-count");
    const pct = byId("workflow-progress-pct");
    const next = byId("workflow-progress-next");

    if (bar) bar.style.width = `${percent}%`;
    if (pct) pct.textContent = `${percent}%`;
    if (count) count.textContent = `${completedSteps} / ${totalSteps} bước hoàn tất`;
    if (next) next.textContent = `Tiếp theo: ${nextStep}`;
  }

  function renderConfirmedState(k) {
    isConfirmed = true;
    const panel = byId("recommendation-panel");
    const panelHeader = byId("panel-header-text");
    const panelMain = byId("panel-main-result");
    const panelDesc = byId("panel-description");
    const btnConfirm = byId("btn-confirm-k");
    const nextStepBar = byId("next-step-bar");
    const nextStepSub = byId("next-step-subtitle");

    if (btnConfirm) btnConfirm.classList.add("hidden");
    if (panelHeader) {
      panelHeader.innerHTML = "✓ K ĐÃ ĐƯỢC XÁC NHẬN";
      panelHeader.classList.remove("text-primary");
      panelHeader.classList.add("text-secondary");
    }
    const star = byId("panel-star-icon");
    if (star) star.classList.add("hidden");

    if (panelMain) {
      panelMain.innerHTML = `
        <div class="font-display-lg text-display-lg text-secondary font-bold mb-xs">K = ${k}</div>
        <p class="font-body-md text-body-md text-on-surface-variant">Cấu hình phân cụm đã sẵn sàng.</p>
      `;
    }

    if (panelDesc) {
      panelDesc.innerHTML = `
        <div class="grid grid-cols-2 gap-sm mt-md bg-surface-container-lowest p-md rounded border border-outline-variant text-xs">
          <div class="text-on-surface-variant">Thuật toán:</div>
          <div class="font-medium text-right text-on-surface">K-Means</div>
          <div class="text-on-surface-variant">Khởi tạo (init):</div>
          <div class="font-medium text-right text-on-surface">k-means++</div>
          <div class="text-on-surface-variant">Số lần chạy (n_init):</div>
          <div class="font-medium text-right text-on-surface">10</div>
          <div class="text-on-surface-variant">Hạt giống (random_state):</div>
          <div class="font-medium text-right text-on-surface">42</div>
        </div>
      `;
    }

    if (panel) {
      panel.classList.remove("border-primary-fixed");
      panel.classList.add("border-secondary", "bg-surface-container");
    }

    if (nextStepSub) nextStepSub.textContent = `Bước tiếp theo: chạy K-Means với K = ${k}`;
    if (nextStepBar) nextStepBar.classList.remove("translate-y-full");

    // Explicitly synchronize workflow progress to 3/5 (60%, Tiếp theo: Phân cụm)
    updateWorkflowProgressUI(3, 5, 60, "Phân cụm");
  }

  function renderState(state) {
    currentState = state;
    if (!state.dataset_loaded) {
      window.location.href = "/data";
      return;
    }
    if (!state.preprocessed) {
      window.location.href = "/eda";
      return;
    }

    if (state.workflow_progress) {
      updateWorkflowProgressUI(
        state.workflow_progress.completed_steps,
        state.workflow_progress.total_steps,
        state.workflow_progress.percent,
        state.workflow_progress.next_step
      );
    } else if (window.renderWorkflowProgress) {
      window.renderWorkflowProgress(state);
    }

    const rowCount = state.row_count || 720;
    if (byId("header-row-count")) byId("header-row-count").textContent = rowCount;

    const kData = state.k_analysis_data;
    if (kData && kData.k_metrics && kData.k_metrics.length > 0) {
      currentKMetrics = kData.k_metrics;
      recommendedK = kData.recommended_k;
      chosenK = kData.selected_k || recommendedK;

      if (kData.k_min && byId("k-min")) byId("k-min").value = kData.k_min;
      if (kData.k_max && byId("k-max")) byId("k-max").value = kData.k_max;

      setChosenK(chosenK);

      if (state.k_selected && kData.selected_k) {
        renderConfirmedState(kData.selected_k);
      }
    } else {
      // Auto-trigger analysis for default range K=2..10
      runAnalysis(2, 10);
    }
  }

  async function runAnalysis(kMin, kMax) {
    const btn = byId("btn-run-analysis");
    const errBox = byId("choose-k-error");
    if (errBox) errBox.classList.add("hidden");

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span> Đang phân tích...';
    }

    try {
      const response = await fetch("/api/k-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ k_min: kMin, k_max: kMax })
      });
      const state = await response.json();
      if (!response.ok) throw new Error(state.detail || "Không thể thực hiện phân tích K.");
      renderState(state);
    } catch (err) {
      if (errBox) {
        errBox.textContent = err.message;
        errBox.classList.remove("hidden");
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-symbols-outlined text-[18px]">play_arrow</span> Phân tích K';
      }
    }
  }

  async function confirmKSelection() {
    if (!chosenK) return;
    const btn = byId("btn-confirm-k");
    const errBox = byId("choose-k-error");
    if (errBox) errBox.classList.add("hidden");

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span> Đang lưu...';
    }

    try {
      const response = await fetch("/api/select-k", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected_k: chosenK })
      });
      const state = await response.json();
      if (!response.ok) throw new Error(state.detail || "Không thể xác nhận K.");
      currentState = state;
      renderConfirmedState(chosenK);
      if (window.renderWorkflowProgress) {
        window.renderWorkflowProgress(state);
      }
    } catch (err) {
      if (errBox) {
        errBox.textContent = err.message;
        errBox.classList.remove("hidden");
      }
      if (btn) {
        btn.disabled = false;
        btn.textContent = `Xác nhận K = ${chosenK}`;
      }
    }
  }

  // Event Listeners
  const btnAnalysis = byId("btn-run-analysis");
  if (btnAnalysis) {
    btnAnalysis.addEventListener("click", () => {
      const kMin = parseInt(byId("k-min")?.value || "2", 10);
      const kMax = parseInt(byId("k-max")?.value || "10", 10);
      runAnalysis(kMin, kMax);
    });
  }

  const btnConfirmK = byId("btn-confirm-k");
  if (btnConfirmK) btnConfirmK.addEventListener("click", confirmKSelection);

  // Initial fetch
  fetch("/api/state")
    .then((res) => res.json())
    .then((state) => renderState(state))
    .catch((err) => console.error("Error loading state:", err));
})();
