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
      name: `Phân phối ${feature}`,
      hovertemplate: "Khoảng: %{x}<br>Số khách hàng: <b>%{y}</b><extra></extra>"
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
      autosize: true,
      hovermode: "closest",
      hoverlabel: {
        bgcolor: "#0b1c30",
        bordercolor: "#0b1c30",
        font: { family: "Inter, sans-serif", size: 12, color: "#ffffff" }
      }
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
      jitter: 0.3,
      hoveron: "points",
      hovertemplate: "<b>%{fullData.name}</b><br>Giá trị: %{y:.2f}<extra></extra>"
    };

    const boxTraceProc = {
      y: procValues,
      type: "box",
      name: "Sau IQR (Clipped)",
      marker: { color: "#006a61" },
      boxpoints: false,
      hoveron: "points",
      hovertemplate: "<b>%{fullData.name}</b><br>Giá trị: %{y:.2f}<extra></extra>"
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
      autosize: true,
      hovermode: "closest",
      hoverlabel: {
        bgcolor: "#0b1c30",
        bordercolor: "#0b1c30",
        font: { family: "Inter, sans-serif", size: 12, color: "#ffffff" }
      }
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

  function updatePipeline(state, animated = false) {
    const rowCount = state.row_count || 720;
    const eda = state.eda_data || {};
    const missingCount = eda.missing_count || 0;
    const outlierCount = eda.total_outliers || 117;

    if (byId("pipe-row-count")) byId("pipe-row-count").textContent = rowCount;
    if (byId("pipe-missing-count")) byId("pipe-missing-count").textContent = missingCount;
    if (byId("pipe-outlier-count")) byId("pipe-outlier-count").textContent = outlierCount;

    const badge = byId("pipeline-overall-badge");
    const n1 = byId("pipe-node-1"), n2 = byId("pipe-node-2"), n3 = byId("pipe-node-3"), n4 = byId("pipe-node-4"), n5 = byId("pipe-node-5");
    const c1 = byId("pipe-conn-1"), c2 = byId("pipe-conn-2"), c3 = byId("pipe-conn-3"), c4 = byId("pipe-conn-4");
    const s1 = byId("pipe-status-1"), s2 = byId("pipe-status-2"), s3 = byId("pipe-status-3"), s4 = byId("pipe-status-4"), s5 = byId("pipe-status-5");
    const t5 = byId("pipe-title-5");

    const checkHtml = (text) => `<span class="material-symbols-outlined text-[12px]" style="font-variation-settings: 'FILL' 1;">check_circle</span> ${text}`;
    const pendingHtml = (text) => `<span class="material-symbols-outlined text-[12px] text-on-surface-variant/40">radio_button_unchecked</span> <span class="text-on-surface-variant/60">${text}</span>`;

    if (!state.preprocessed) {
      if (badge) {
        badge.className = "self-start sm:self-auto px-3 py-1 bg-surface-container-high text-on-surface-variant rounded-full text-xs font-semibold flex items-center gap-1";
        badge.innerHTML = '<span class="material-symbols-outlined text-[14px]">pending</span> Chờ tiền xử lý';
      }
      if (n1) n1.className = "relative z-10 w-11 h-11 rounded-full bg-primary text-on-primary flex items-center justify-center shadow-sm ring-4 ring-primary/20 shrink-0 transition-all duration-300";
      if (s1) s1.innerHTML = checkHtml("Đã sẵn sàng");

      [n2, n3, n4, n5].forEach((n) => {
        if (n) n.className = "relative z-10 w-11 h-11 rounded-full bg-surface-container-high text-on-surface-variant/40 flex items-center justify-center shadow-sm ring-4 ring-white shrink-0 transition-all duration-300";
      });
      [c1, c2, c3, c4].forEach((c) => {
        if (c) c.style.width = "0%";
      });
      if (s2) s2.innerHTML = pendingHtml("Chờ xử lý");
      if (s3) s3.innerHTML = pendingHtml("Chờ xử lý");
      if (s4) s4.innerHTML = pendingHtml("Chờ xử lý");
      if (s5) s5.innerHTML = pendingHtml("Chưa kích hoạt");
      if (t5) t5.className = "font-label-sm text-xs font-bold text-on-surface-variant/70";
      return;
    }

    const completeNode = (node, isLast = false) => {
      if (!node) return;
      node.className = isLast
        ? "relative z-10 w-11 h-11 rounded-full bg-secondary text-on-secondary flex items-center justify-center shadow-sm ring-4 ring-secondary/25 shrink-0 transition-all duration-300"
        : "relative z-10 w-11 h-11 rounded-full bg-secondary text-on-secondary flex items-center justify-center shadow-sm ring-4 ring-white shrink-0 transition-all duration-300";
    };

    const pulseNode = (node) => {
      if (!node) return;
      node.style.transform = "scale(1.15)";
      setTimeout(() => { node.style.transform = "scale(1)"; }, 220);
    };

    if (animated) {
      if (badge) {
        badge.className = "self-start sm:self-auto px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-semibold flex items-center gap-1";
        badge.innerHTML = '<span class="material-symbols-outlined text-[14px] animate-spin">sync</span> Đang chuẩn hóa...';
      }

      completeNode(n1);
      if (s1) s1.innerHTML = checkHtml("Hoàn tất");

      setTimeout(() => {
        if (c1) c1.style.width = "100%";
        setTimeout(() => {
          completeNode(n2);
          pulseNode(n2);
          if (s2) s2.innerHTML = checkHtml("Hoàn tất");
        }, 180);
      }, 100);

      setTimeout(() => {
        if (c2) c2.style.width = "100%";
        setTimeout(() => {
          completeNode(n3);
          pulseNode(n3);
          if (s3) s3.innerHTML = checkHtml("Hoàn tất");
        }, 180);
      }, 350);

      setTimeout(() => {
        if (c3) c3.style.width = "100%";
        setTimeout(() => {
          completeNode(n4);
          pulseNode(n4);
          if (s4) s4.innerHTML = checkHtml("Hoàn tất");
        }, 180);
      }, 600);

      setTimeout(() => {
        if (c4) c4.style.width = "100%";
        setTimeout(() => {
          completeNode(n5, true);
          pulseNode(n5);
          if (t5) t5.className = "font-label-sm text-xs font-bold text-secondary";
          if (s5) s5.innerHTML = checkHtml("Sẵn sàng");
          if (badge) {
            badge.className = "self-start sm:self-auto px-3 py-1 bg-secondary-container/40 text-on-secondary-container rounded-full text-xs font-semibold flex items-center gap-1";
            badge.innerHTML = '<span class="material-symbols-outlined text-[14px]">verified</span> 5/5 Hoàn tất';
          }
        }, 180);
      }, 850);
    } else {
      if (badge) {
        badge.className = "self-start sm:self-auto px-3 py-1 bg-secondary-container/40 text-on-secondary-container rounded-full text-xs font-semibold flex items-center gap-1";
        badge.innerHTML = '<span class="material-symbols-outlined text-[14px]">verified</span> 5/5 Hoàn tất';
      }
      [n1, n2, n3, n4].forEach((n) => completeNode(n));
      completeNode(n5, true);
      [c1, c2, c3, c4].forEach((c) => { if (c) c.style.width = "100%"; });
      if (s1) s1.innerHTML = checkHtml("Hoàn tất");
      if (s2) s2.innerHTML = checkHtml("Hoàn tất");
      if (s3) s3.innerHTML = checkHtml("Hoàn tất");
      if (s4) s4.innerHTML = checkHtml("Hoàn tất");
      if (s5) s5.innerHTML = checkHtml("Sẵn sàng");
      if (t5) t5.className = "font-label-sm text-xs font-bold text-secondary";
    }
  }

  function renderEDAState(state, animated = false) {
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
    const strategySelect = byId("outlier-strategy");
    const btnPreprocess = byId("btn-run-preprocess");

    if (strategySelect && state.outlier_strategy) {
      strategySelect.value = state.outlier_strategy;
    }

    if (actionBanner) {
      actionBanner.classList.remove("hidden");
    }

    if (!state.preprocessed) {
      if (resultsContainer) resultsContainer.classList.add("opacity-50", "pointer-events-none");
      if (btnToChooseK) {
        btnToChooseK.classList.add("opacity-60", "pointer-events-none");
      }
      if (btnPreprocess) {
        btnPreprocess.innerHTML = '<span class="material-symbols-outlined text-[20px]">play_arrow</span> Xử lý dữ liệu';
      }
      updatePipeline(state, false);
      return;
    }

    if (resultsContainer) resultsContainer.classList.remove("hidden", "opacity-50", "pointer-events-none");
    if (btnToChooseK) {
      btnToChooseK.classList.remove("opacity-60", "pointer-events-none");
    }
    if (btnPreprocess) {
      btnPreprocess.innerHTML = '<span class="material-symbols-outlined text-[20px]">refresh</span> Xử lý lại dữ liệu';
    }

    const eda = state.eda_data || {};
    const beforeAfter = eda.before_after || {};
    const corr = eda.correlation || {};
    const statsTable = eda.stats_table || {};

    // 1. Update Pipeline Centerpiece
    updatePipeline(state, animated);

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
        const labelText = state.outlier_strategy === "keep" ? "Đã xử lý (Keep)" : "Đã xử lý (IQR)";

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
            <td class="py-2 px-4 text-secondary text-xs"><span class="px-2 py-0.5 rounded bg-secondary-container/40 text-on-secondary-container font-medium">${labelText}</span></td>
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
    const strategySelect = byId("outlier-strategy");
    const strategy = strategySelect ? strategySelect.value : "iqr_clip";
    if (errorBox) errorBox.classList.add("hidden");

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-[20px]">progress_activity</span> Đang xử lý...';
    }

    try {
      const response = await fetch("/api/preprocess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ outlier_strategy: strategy })
      });
      const state = await response.json();
      if (!response.ok) throw new Error(state.detail || "Không thể thực hiện tiền xử lý.");
      renderEDAState(state, true);
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
