(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  let currentState = null;
  let activeFeature = "Recency";

  function formatNumber(num) {
    if (num === null || num === undefined) return "—";
    return Number(num).toLocaleString("vi-VN", { maximumFractionDigits: 2 });
  }

  function renderCharts(feature, chartData, beforeAfter) {
    if (!window.Plotly || !chartData || !chartData[feature]) return;

    const rawValues = chartData[feature].raw || [];
    const procValues = chartData[feature].processed || [];
    const bounds = (beforeAfter && beforeAfter[feature]) || {};

    // 1. Histogram (Processed Data Distribution)
    const histTrace = {
      x: procValues,
      type: "histogram",
      autobinx: true,
      marker: {
        color: "#3525cd",
        opacity: 0.85,
        line: { color: "#2114a8", width: 1 }
      },
      name: `Phân phối ${feature}`
    };

    const histLayout = {
      margin: { t: 15, r: 15, b: 35, l: 45 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { family: "Inter, sans-serif", size: 11, color: "#464555" },
      xaxis: {
        title: { text: feature, font: { size: 11, color: "#464555" } },
        gridcolor: "#e5eeff",
        zeroline: false
      },
      yaxis: {
        title: { text: "Số lượng khách hàng", font: { size: 10, color: "#464555" } },
        gridcolor: "#e5eeff",
        zeroline: false
      },
      showlegend: false,
      autosize: true
    };

    const config = { responsive: true, displayModeBar: false };
    Plotly.newPlot("chart-histogram", [histTrace], histLayout, config);

    // 2. Boxplot (Before vs After IQR comparison)
    const boxTraceRaw = {
      y: rawValues,
      type: "box",
      name: "Trước IQR (Gốc)",
      marker: { color: "#ba1a1a" },
      boxpoints: "outliers",
      jitter: 0.3
    };

    const boxTraceProc = {
      y: procValues,
      type: "box",
      name: "Sau IQR (Clipped)",
      marker: { color: "#006a61" },
      boxpoints: false
    };

    const boxLayout = {
      margin: { t: 15, r: 15, b: 35, l: 45 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { family: "Inter, sans-serif", size: 11, color: "#464555" },
      yaxis: {
        title: { text: `Giá trị ${feature}`, font: { size: 10, color: "#464555" } },
        gridcolor: "#e5eeff",
        zeroline: false
      },
      xaxis: {
        gridcolor: "#e5eeff",
        zeroline: false
      },
      showlegend: true,
      legend: { orientation: "h", y: -0.2, x: 0.1, font: { size: 10 } },
      autosize: true
    };

    Plotly.newPlot("chart-boxplot", [boxTraceRaw, boxTraceProc], boxLayout, config);
  }

  function setFeatureTab(feature) {
    activeFeature = feature;
    const tabs = {
      Recency: byId("tab-recency"),
      Frequency: byId("tab-frequency"),
      Monetary: byId("tab-monetary")
    };

    Object.keys(tabs).forEach((key) => {
      const tab = tabs[key];
      if (!tab) return;
      if (key === feature) {
        tab.className = "flex-1 py-3 px-4 text-center font-label-sm font-bold text-primary border-b-2 border-primary bg-primary/5 transition-all";
      } else {
        tab.className = "flex-1 py-3 px-4 text-center font-label-sm font-bold text-on-surface-variant hover:bg-surface-container/50 transition-all";
      }
    });

    if (currentState && currentState.eda_data && currentState.eda_data.chart_data) {
      renderCharts(feature, currentState.eda_data.chart_data, currentState.eda_data.before_after);
    }
  }

  function renderEDAState(state) {
    currentState = state;
    if (!state.dataset_loaded) {
      window.location.href = "/data";
      return;
    }

    window.renderWorkflowProgress(state);

    const rowCount = state.row_count || 0;
    const countBadge = byId("header-customer-count");
    if (countBadge) countBadge.textContent = rowCount;

    const actionBanner = byId("preprocess-action-banner");
    const resultsContainer = byId("eda-results-container");

    const btnToChooseK = byId("btn-to-choose-k");
    if (!state.preprocessed) {
      if (actionBanner) actionBanner.classList.remove("hidden");
      if (resultsContainer) resultsContainer.classList.add("opacity-50", "pointer-events-none");
      if (btnToChooseK) {
        btnToChooseK.classList.add("opacity-60", "pointer-events-none");
      }
      return;
    }

    if (actionBanner) actionBanner.classList.add("hidden");
    if (resultsContainer) resultsContainer.classList.remove("hidden", "opacity-50", "pointer-events-none");
    if (btnToChooseK) {
      btnToChooseK.classList.remove("opacity-60", "pointer-events-none");
    }

    const eda = state.eda_data || {};
    const beforeAfter = eda.before_after || {};
    const corr = eda.correlation || {};
    const statsTable = eda.stats_table || {};

    // 1. Pipeline Centerpiece
    const pipeProgress = byId("pipeline-progress");
    if (pipeProgress) pipeProgress.style.width = "80%";

    const steps = document.querySelectorAll(".pipeline-step");
    steps.forEach((step) => {
      const delay = parseInt(step.getAttribute("data-delay") || "100", 10);
      setTimeout(() => {
        step.style.opacity = "1";
        step.style.transform = "translateY(0)";
      }, delay);
    });

    if (byId("pipe-row-count")) byId("pipe-row-count").textContent = eda.row_count || rowCount;
    if (byId("pipe-missing-count")) byId("pipe-missing-count").textContent = eda.missing_count || 0;
    if (byId("pipe-outlier-count")) byId("pipe-outlier-count").textContent = eda.total_outliers || 0;

    // 2. Metrics summary
    if (byId("stat-row-count")) byId("stat-row-count").textContent = eda.row_count || rowCount;
    if (byId("stat-feature-count")) byId("stat-feature-count").textContent = eda.feature_count || 3;
    if (byId("stat-missing-count")) byId("stat-missing-count").textContent = eda.missing_count || 0;

    // 3. Before/After cards
    if (beforeAfter.Recency) {
      const r = beforeAfter.Recency;
      if (byId("recency-raw-max")) byId("recency-raw-max").textContent = formatNumber(r.raw_max);
      if (byId("recency-clipped-max")) byId("recency-clipped-max").textContent = formatNumber(r.clipped_max);
      if (byId("recency-clipped-pct")) byId("recency-clipped-pct").textContent = `Giới hạn cực trị: ${r.pct_clipped}%`;
      if (byId("recency-q1")) byId("recency-q1").textContent = formatNumber(r.q1);
      if (byId("recency-q3")) byId("recency-q3").textContent = formatNumber(r.q3);
      if (byId("recency-outliers")) byId("recency-outliers").textContent = r.outliers;
    }

    if (beforeAfter.Frequency) {
      const f = beforeAfter.Frequency;
      if (byId("frequency-raw-max")) byId("frequency-raw-max").textContent = formatNumber(f.raw_max);
      if (byId("frequency-clipped-max")) byId("frequency-clipped-max").textContent = formatNumber(f.clipped_max);
      if (byId("frequency-clipped-pct")) byId("frequency-clipped-pct").textContent = `Giới hạn cực trị: ${f.pct_clipped}%`;
      if (byId("frequency-q1")) byId("frequency-q1").textContent = formatNumber(f.q1);
      if (byId("frequency-q3")) byId("frequency-q3").textContent = formatNumber(f.q3);
      if (byId("frequency-outliers")) byId("frequency-outliers").textContent = f.outliers;
    }

    if (beforeAfter.Monetary) {
      const m = beforeAfter.Monetary;
      if (byId("monetary-raw-max")) byId("monetary-raw-max").textContent = formatNumber(m.raw_max);
      if (byId("monetary-clipped-max")) byId("monetary-clipped-max").textContent = formatNumber(m.clipped_max);
      if (byId("monetary-clipped-pct")) byId("monetary-clipped-pct").textContent = `Giới hạn cực trị: ${m.pct_clipped}%`;
      if (byId("monetary-q1")) byId("monetary-q1").textContent = formatNumber(m.q1);
      if (byId("monetary-q3")) byId("monetary-q3").textContent = formatNumber(m.q3);
      if (byId("monetary-outliers")) byId("monetary-outliers").textContent = m.outliers;
    }

    // 4. Correlation matrix
    if (corr.Recency && corr.Frequency && corr.Monetary) {
      const getFormatted = (val) => (val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2));
      if (byId("corr-rr")) byId("corr-rr").textContent = corr.Recency.Recency.toFixed(2);
      if (byId("corr-rf")) byId("corr-rf").textContent = getFormatted(corr.Recency.Frequency);
      if (byId("corr-rm")) byId("corr-rm").textContent = getFormatted(corr.Recency.Monetary);
      if (byId("corr-fr")) byId("corr-fr").textContent = getFormatted(corr.Frequency.Recency);
      if (byId("corr-ff")) byId("corr-ff").textContent = corr.Frequency.Frequency.toFixed(2);
      if (byId("corr-fm")) byId("corr-fm").textContent = getFormatted(corr.Frequency.Monetary);
      if (byId("corr-mr")) byId("corr-mr").textContent = getFormatted(corr.Monetary.Recency);
      if (byId("corr-mf")) byId("corr-mf").textContent = getFormatted(corr.Monetary.Frequency);
      if (byId("corr-mm")) byId("corr-mm").textContent = corr.Monetary.Monetary.toFixed(2);
    }

    // 5. Descriptive statistics table
    const tableBody = byId("stats-table-body");
    if (tableBody && statsTable.raw && statsTable.processed) {
      const features = ["Recency", "Frequency", "Monetary"];
      const rowsHtml = [];

      features.forEach((feat) => {
        const raw = statsTable.raw[feat] || {};
        const proc = statsTable.processed[feat] || {};

        rowsHtml.push(`
          <tr class="hover:bg-surface-container-lowest transition-colors border-t border-outline-variant/50">
            <td rowspan="2" class="py-3 px-4 font-bold text-on-surface align-middle border-r border-outline-variant/30">${feat}</td>
            <td class="py-2 px-4 text-on-surface-variant text-xs"><span class="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-medium">Gốc (Raw)</span></td>
            <td class="py-2 px-4 text-right font-medium">${formatNumber(raw.mean)}</td>
            <td class="py-2 px-4 text-right text-on-surface-variant">${formatNumber(raw.std)}</td>
            <td class="py-2 px-4 text-right text-on-surface-variant">${formatNumber(raw.min)}</td>
            <td class="py-2 px-4 text-right text-on-surface-variant">${formatNumber(raw["25%"])}</td>
            <td class="py-2 px-4 text-right font-semibold text-primary">${formatNumber(raw["50%"])}</td>
            <td class="py-2 px-4 text-right text-on-surface-variant">${formatNumber(raw["75%"])}</td>
            <td class="py-2 px-4 text-right font-medium text-error">${formatNumber(raw.max)}</td>
          </tr>
          <tr class="hover:bg-surface-container-lowest transition-colors bg-surface-container-low/20">
            <td class="py-2 px-4 text-secondary text-xs"><span class="px-2 py-0.5 rounded bg-secondary-container/40 text-on-secondary-container font-medium">Đã xử lý (IQR)</span></td>
            <td class="py-2 px-4 text-right font-medium text-secondary">${formatNumber(proc.mean)}</td>
            <td class="py-2 px-4 text-right text-on-surface-variant">${formatNumber(proc.std)}</td>
            <td class="py-2 px-4 text-right text-on-surface-variant">${formatNumber(proc.min)}</td>
            <td class="py-2 px-4 text-right text-on-surface-variant">${formatNumber(proc["25%"])}</td>
            <td class="py-2 px-4 text-right font-semibold text-secondary">${formatNumber(proc["50%"])}</td>
            <td class="py-2 px-4 text-right text-on-surface-variant">${formatNumber(proc["75%"])}</td>
            <td class="py-2 px-4 text-right font-medium text-secondary">${formatNumber(proc.max)}</td>
          </tr>
        `);
      });

      tableBody.innerHTML = rowsHtml.join("");
    }

    // 6. Render charts
    setFeatureTab(activeFeature);
  }

  // Preprocess API trigger
  async function runPreprocess() {
    const btn = byId("btn-run-preprocess");
    const errorBox = byId("eda-error");
    if (errorBox) errorBox.classList.add("hidden");

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-[20px]">progress_activity</span> Đang xử lý...';
    }

    try {
      const response = await fetch("/api/preprocess", { method: "POST" });
      const state = await response.json();
      if (!response.ok) throw new Error(state.detail || "Không thể thực hiện tiền xử lý.");
      renderEDAState(state);
    } catch (err) {
      if (errorBox) {
        errorBox.textContent = err.message;
        errorBox.classList.remove("hidden");
      }
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-symbols-outlined text-[20px]">play_arrow</span> Thử lại xử lý dữ liệu';
      }
    }
  }

  // Event Listeners
  const btnPreprocess = byId("btn-run-preprocess");
  if (btnPreprocess) btnPreprocess.addEventListener("click", runPreprocess);

  const tabR = byId("tab-recency");
  const tabF = byId("tab-frequency");
  const tabM = byId("tab-monetary");

  if (tabR) tabR.addEventListener("click", () => setFeatureTab("Recency"));
  if (tabF) tabF.addEventListener("click", () => setFeatureTab("Frequency"));
  if (tabM) tabM.addEventListener("click", () => setFeatureTab("Monetary"));

  // Initial State load
  fetch("/api/state")
    .then((res) => res.json())
    .then((state) => renderEDAState(state))
    .catch((err) => console.error("Error loading state:", err));
})();
