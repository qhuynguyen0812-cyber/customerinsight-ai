(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const CLUSTER_COLORS = [
    "#4f46e5", // Primary indigo
    "#006a61", // Teal
    "#3323cc", // Deep indigo
    "#a44100", // Warm amber
    "#ba1a1a", // Crimson
    "#00838f", // Cyan
    "#6a1b9a", // Purple
    "#2e7d32", // Forest green
    "#d81b60", // Pink
    "#ef6c00"  // Orange
  ];

  let currentState = null;

  function getColor(index) {
    return CLUSTER_COLORS[index % CLUSTER_COLORS.length];
  }

  function updateWorkflowProgressUI(completedSteps, totalSteps, percent, nextStep) {
    if (window.renderWorkflowProgress) {
      window.renderWorkflowProgress({
        workflow_progress: {
          completed_steps: completedSteps,
          total_steps: totalSteps,
          percent: percent,
          next_step: nextStep
        }
      });
      return;
    }
    const bar = byId("workflow-progress-bar");
    const count = byId("workflow-progress-count");
    const pct = byId("workflow-progress-pct");
    const next = byId("workflow-progress-next");

    if (bar) bar.style.width = `${percent}%`;
    if (pct) pct.textContent = `${percent}%`;
    if (count) count.textContent = `${completedSteps} / ${totalSteps} bước hoàn tất`;
    if (next) {
      if (completedSteps >= 5 || nextStep === "Phân tích hoàn tất" || percent >= 100) {
        next.className = "font-label-sm text-[10px] text-primary font-semibold mt-2 border-t border-outline-variant/30 pt-2 flex items-center gap-1";
        next.innerHTML = `<span class="material-symbols-outlined text-xs" style="font-size: 14px; font-variation-settings: 'FILL' 1;">check_circle</span> Phân tích hoàn tất`;
      } else {
        next.className = "font-label-sm text-[10px] text-on-surface-variant mt-2 border-t border-outline-variant/30 pt-2";
        next.textContent = `Tiếp theo: ${nextStep}`;
      }
    }
  }

  function renderDistribution(profiles) {
    const container = byId("distribution-container");
    if (!container || !profiles) return;

    container.innerHTML = profiles
      .map((p, idx) => {
        const color = getColor(p.cluster_id);
        const distId = `dist-${p.cluster_id + 1}`;
        return `
          <div class="transition-all duration-300" id="${distId}">
            <div class="flex justify-between font-label-sm text-label-sm mb-1">
              <span style="color: ${color};" class="font-semibold">${p.cluster_label} (${p.percentage}%)</span>
              <span class="text-on-surface-variant">${p.count} KH</span>
            </div>
            <div class="w-full bg-surface-variant rounded-full h-2">
              <div class="h-2 rounded-full transition-all duration-700" style="width: ${p.percentage}%; background-color: ${color};"></div>
            </div>
          </div>
        `;
      })
      .join("");
  }

  function renderProfileCards(profiles) {
    const container = byId("profile-cards-container");
    if (!container || !profiles) return;

    // Adjust grid columns dynamically
    const k = profiles.length;
    if (k === 2) {
      container.className = "grid grid-cols-1 md:grid-cols-2 gap-grid-gutter";
    } else if (k === 4) {
      container.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-grid-gutter";
    } else if (k >= 5) {
      container.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-grid-gutter";
    } else {
      container.className = "grid grid-cols-1 md:grid-cols-3 gap-grid-gutter";
    }

    container.innerHTML = profiles
      .map((p, idx) => {
        const color = getColor(p.cluster_id);
        const cardId = `profile-card-${p.cluster_id + 1}`;
        return `
          <div id="${cardId}" class="profile-card bg-surface-container-lowest border-t-4 rounded-lg border border-outline-variant shadow-[0_4px_6px_-1px_rgba(0,0,0,0.05)] p-md cursor-pointer transition-all duration-300 flex flex-col" style="border-top-color: ${color};">
            <div class="flex items-center justify-between mb-sm">
              <div class="flex items-center gap-sm">
                <div class="w-4 h-4 rounded-full" style="background-color: ${color};"></div>
                <h4 class="font-title-md text-title-md font-bold text-on-surface">${p.cluster_label}</h4>
              </div>
              <span class="text-xs text-on-surface-variant font-medium">${p.count} KH (${p.percentage}%)</span>
            </div>
            <p class="font-body-md text-body-md font-bold text-primary mb-md min-h-[48px]">${p.segment_name}</p>
            <div class="space-y-sm mb-md flex-1">
              <div class="flex justify-between border-b border-outline-variant pb-1">
                <span class="font-label-sm text-label-sm text-on-surface-variant">R (Recency)</span>
                <span class="font-body-md text-body-md font-semibold text-on-surface">${p.mean_recency}</span>
              </div>
              <div class="flex justify-between border-b border-outline-variant pb-1">
                <span class="font-label-sm text-label-sm text-on-surface-variant">F (Frequency)</span>
                <span class="font-body-md text-body-md font-semibold text-on-surface">${p.mean_frequency}</span>
              </div>
              <div class="flex justify-between">
                <span class="font-label-sm text-label-sm text-on-surface-variant">M (Monetary)</span>
                <span class="font-body-md text-body-md font-semibold text-on-surface">${p.mean_monetary}</span>
              </div>
            </div>
            <p class="font-body-sm text-sm text-on-surface-variant"><span class="font-semibold text-on-surface">✦ Nhận xét:</span> ${p.recommendation}</p>
          </div>
        `;
      })
      .join("");

    // Attach hover effects linking cards and distribution bars
    profiles.forEach((p) => {
      const card = byId(`profile-card-${p.cluster_id + 1}`);
      const dist = byId(`dist-${p.cluster_id + 1}`);

      if (card && dist) {
        card.addEventListener("mouseenter", () => {
          dist.classList.add("scale-105", "opacity-100");
          profiles.filter((other) => other.cluster_id !== p.cluster_id).forEach((other) => {
            const otherDist = byId(`dist-${other.cluster_id + 1}`);
            if (otherDist) otherDist.classList.add("opacity-40");
          });
        });

        card.addEventListener("mouseleave", () => {
          profiles.forEach((other) => {
            const otherDist = byId(`dist-${other.cluster_id + 1}`);
            if (otherDist) otherDist.classList.remove("scale-105", "opacity-40", "opacity-100");
          });
        });
      }
    });
  }

  function updateTracker(step) {
    const tracker = byId("process-tracker");
    if (!tracker) return;
    const items = tracker.querySelectorAll("div");

    items.forEach((item, i) => {
      if (i < step) {
        item.className = "flex items-center gap-1 text-on-surface-variant opacity-50";
      } else if (i === step) {
        item.className = "flex items-center gap-1 text-primary font-medium";
      } else {
        item.className = "flex items-center gap-1 text-on-surface-variant opacity-50";
      }
    });
  }

  function runScatterAnimation(points, centers, iterations) {
    const plotArea = byId("scatter-plot");
    const titleEl = byId("viz-title");
    if (!plotArea) return;

    if (!points || points.length === 0) {
      plotArea.innerHTML = `<div class="flex items-center justify-center h-full text-on-surface-variant text-sm">Không có dữ liệu hiển thị.</div>`;
      return;
    }

    const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches === true;

    if (isReducedMotion) {
      if (titleEl) titleEl.textContent = `Hội tụ hoàn tất · ${iterations} lần lặp`;
      renderFinalScatter(plotArea, points, centers);
      updateTracker(3);
      return;
    }

    // Step 0: Neutral points
    updateTracker(0);
    if (titleEl) titleEl.textContent = "Khởi tạo dữ liệu...";

    let pointsHTML = points
      .map(
        (p, i) =>
          `<div id="pt-${i}" class="point absolute w-2 h-2 rounded-full opacity-60 bg-gray-400" style="left: ${p.x}%; top: ${p.y}%;"></div>`
      )
      .join("");
    plotArea.innerHTML = pointsHTML;

    setTimeout(() => {
      // Step 1: Centroids appear
      updateTracker(1);
      if (titleEl) titleEl.textContent = "Quá trình hội tụ · Khởi tạo centroids...";
      let centroidsHTML = centers
        .map(
          (c, i) =>
            `<div id="ct-${i}" class="point absolute w-6 h-6 rounded-md bg-white border-4 shadow-sm z-10 flex items-center justify-center transition-all duration-1000" style="left: 50%; top: 50%; border-color: ${getColor(c.cluster)}; transform: translate(-50%, -50%);">
              <span class="material-symbols-outlined text-[12px]" style="color:${getColor(c.cluster)}">close</span>
            </div>`
        )
        .join("");
      plotArea.insertAdjacentHTML("beforeend", centroidsHTML);

      setTimeout(() => {
        // Step 2: Assign colors to points
        updateTracker(2);
        if (titleEl) titleEl.textContent = `Quá trình hội tụ · Lần lặp ${Math.max(1, Math.floor(iterations / 2))}...`;
        points.forEach((p, i) => {
          const ptEl = byId(`pt-${i}`);
          if (ptEl) ptEl.style.backgroundColor = getColor(p.cluster);
        });

        setTimeout(() => {
          // Step 3: Move centroids to final positions
          centers.forEach((c, i) => {
            const ctEl = byId(`ct-${i}`);
            if (ctEl) {
              ctEl.style.left = `${c.x}%`;
              ctEl.style.top = `${c.y}%`;
            }
          });

          setTimeout(() => {
            updateTracker(3);
            if (titleEl) titleEl.textContent = `Hội tụ hoàn tất · ${iterations} lần lặp`;
          }, 800);
        }, 600);
      }, 500);
    }, 400);
  }

  function renderFinalScatter(area, points, centers) {
    let html = points
      .map(
        (p) =>
          `<div class="absolute w-2 h-2 rounded-full opacity-60" style="left: ${p.x}%; top: ${p.y}%; background-color: ${getColor(p.cluster)};"></div>`
      )
      .join("");

    html += centers
      .map(
        (c) =>
          `<div class="absolute w-6 h-6 rounded-md bg-white border-4 shadow-sm z-10 flex items-center justify-center" style="left: ${c.x}% !important; top: ${c.y}% !important; border-color: ${getColor(c.cluster)}; transform: translate(-50%, -50%);">
            <span class="material-symbols-outlined text-[12px]" style="color:${getColor(c.cluster)}">close</span>
          </div>`
      )
      .join("");

    area.innerHTML = html;
  }

  function renderClusteringState(state) {
    currentState = state;
    if (!state.dataset_loaded) {
      window.location.href = "/data";
      return;
    }
    if (!state.preprocessed) {
      window.location.href = "/eda";
      return;
    }
    if (!state.k_selected && !state.selected_k) {
      window.location.href = "/choose-k";
      return;
    }

    const kVal = state.selected_k ?? (state.clustering_data ? state.clustering_data.k : null);
    const rowCount = state.row_count ?? 0;
    const prefs = state.solver_preferences ?? { max_iter: 300, tol: 0.0001 };
    if (byId("solver-max-iter")) byId("solver-max-iter").value = prefs.max_iter ?? 300;
    if (byId("solver-tol")) byId("solver-tol").value = prefs.tol ?? 0.0001;
    if (byId("config-maxiter-val")) byId("config-maxiter-val").textContent = prefs.max_iter ?? 300;
    if (byId("config-tol-val")) byId("config-tol-val").textContent = prefs.tol ?? 0.0001;

    // Header & Config
    if (byId("header-status-text")) byId("header-status-text").textContent = `Trạng thái: K = ${kVal} · ${rowCount} khách hàng`;
    if (byId("config-k-val")) byId("config-k-val").textContent = kVal;

    const data = state.clustering_data;
    if (data && data.profiles && data.profiles.length > 0) {
      if (byId("results-area")) byId("results-area").classList.remove("hidden");
      // Config values
      if (byId("config-init-val")) byId("config-init-val").textContent = data.init;
      if (byId("config-ninit-val")) byId("config-ninit-val").textContent = data.n_init;
      if (byId("config-rs-val")) byId("config-rs-val").textContent = data.random_state;
      if (byId("config-maxiter-val")) byId("config-maxiter-val").textContent = data.max_iter;
      if (byId("config-tol-val")) byId("config-tol-val").textContent = data.tol;

      // Summary text
      const largest = [...data.profiles].sort((a, b) => b.count - a.count)[0];
      const summaryText = `${rowCount} khách hàng đã được chia thành ${data.k} phân khúc. ${largest.cluster_label} là nhóm lớn nhất với ${largest.percentage}% khách hàng (${largest.count} KH).`;
      if (byId("summary-paragraph")) byId("summary-paragraph").textContent = summaryText;

      // Detail accordion
      if (byId("detail-k")) byId("detail-k").textContent = data.k;
      if (byId("detail-init")) byId("detail-init").textContent = data.init;
      if (byId("detail-ninit")) byId("detail-ninit").textContent = data.n_init;
      if (byId("detail-rs")) byId("detail-rs").textContent = data.random_state;
      if (byId("detail-maxiter")) byId("detail-maxiter").textContent = data.max_iter;
      if (byId("detail-tol")) byId("detail-tol").textContent = data.tol;
      if (byId("detail-inertia")) byId("detail-inertia").textContent = data.inertia.toFixed(4);
      if (byId("detail-silhouette")) byId("detail-silhouette").textContent = data.silhouette.toFixed(4);
      if (byId("detail-iterations")) byId("detail-iterations").textContent = data.iterations;
      if (byId("detail-runtime")) byId("detail-runtime").textContent = data.runtime_seconds.toFixed(2);

      // Post-run metrics
      if (byId("metric-row-count")) byId("metric-row-count").textContent = rowCount;
      if (byId("metric-cluster-count")) byId("metric-cluster-count").textContent = data.k;
      if (byId("metric-iterations")) byId("metric-iterations").textContent = data.iterations;
      if (byId("metric-silhouette")) byId("metric-silhouette").textContent = data.silhouette.toFixed(4);
      if (byId("metric-inertia")) byId("metric-inertia").textContent = data.inertia.toFixed(4);
      if (byId("metric-runtime")) byId("metric-runtime").textContent = data.runtime_seconds.toFixed(2);

      // Render distribution and cards
      renderDistribution(data.profiles);
      renderProfileCards(data.profiles);

      // Run scatter animation
      runScatterAnimation(data.points_2d, data.centers_2d, data.iterations);

      // Synchronize workflow progress from canonical state
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
    } else {
      if (byId("results-area")) byId("results-area").classList.add("hidden");
    }
  }

  async function runClustering() {
    const btn = byId("btn-run-clustering");
    const errBox = byId("clustering-error");
    if (errBox) errBox.classList.add("hidden");

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span> Đang chạy K-Means...';
    }

    try {
      const response = await fetch("/api/cluster", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const state = await response.json();
      if (!response.ok) throw new Error(state.detail || "Không thể thực hiện phân cụm K-Means.");
      renderClusteringState(state);
      if (window.renderWorkflowProgress) {
        window.renderWorkflowProgress(state);
      }
    } catch (err) {
      if (errBox) {
        errBox.textContent = err.message;
        errBox.classList.remove("hidden");
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-symbols-outlined text-[18px]">play_arrow</span> Chạy K-Means';
      }
    }
  }

  async function saveSolverPreferences() {
    const maxIterInput = byId("solver-max-iter");
    const tolInput = byId("solver-tol");
    const errBox = byId("clustering-error");
    if (!maxIterInput || !tolInput) return;
    const max_iter = Number(maxIterInput.value);
    const tol = Number(tolInput.value);
    if (!Number.isInteger(max_iter) || max_iter < 1 || !Number.isFinite(tol) || tol <= 0) {
      if (errBox) {
        errBox.textContent = "max_iter phải là số nguyên dương và tol phải là số hữu hạn dương.";
        errBox.classList.remove("hidden");
      }
      return;
    }
    try {
      const response = await fetch("/api/solver-preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_iter, tol })
      });
      const state = await response.json();
      if (!response.ok) throw new Error(state.detail || "Không thể lưu cấu hình solver.");
      renderClusteringState(state);
    } catch (err) {
      if (errBox) {
        errBox.textContent = err.message;
        errBox.classList.remove("hidden");
      }
    }
  }

  const btnRun = byId("btn-run-clustering");
  if (btnRun) btnRun.addEventListener("click", runClustering);

  const btnToggle = byId("btn-toggle-advanced");
  const advancedPanel = byId("advanced-config-panel");
  if (btnToggle && advancedPanel) {
    btnToggle.addEventListener("click", () => advancedPanel.classList.toggle("hidden"));
  }
  if (byId("solver-max-iter")) byId("solver-max-iter").addEventListener("change", saveSolverPreferences);
  if (byId("solver-tol")) byId("solver-tol").addEventListener("change", saveSolverPreferences);

  // Initial load
  fetch("/api/state")
    .then((res) => res.json())
    .then((state) => renderClusteringState(state))
    .catch((err) => console.error("Error loading state in clustering.js:", err));
})();
