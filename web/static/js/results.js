(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);
  const CLUSTER_COLORS = [
    "#3525cd", // Primary Indigo
    "#006a61", // Secondary Teal
    "#8b5cf6", // Tertiary Purple
    "#a44100", // Warm Amber
    "#ba1a1a", // Crimson
    "#00838f", // Cyan
    "#6a1b9a", // Deep Purple
    "#2e7d32", // Forest Green
    "#d81b60", // Pink
    "#ef6c00"  // Orange
  ];

  let resultsData = null;
  let currentFilter = "all";
  let searchQuery = "";

  function getColor(index) {
    return CLUSTER_COLORS[index % CLUSTER_COLORS.length];
  }

  function getClusterInfoMap(profiles) {
    const map = {};
    profiles.forEach((p) => {
      map[p.cluster_id] = {
        label: p.cluster_label,
        name: p.segment_name,
        hex: getColor(p.cluster_id),
        means: { r: p.mean_recency, f: p.mean_frequency, m: p.mean_monetary },
        desc: p.insight || "Phân khúc khách hàng.",
        total: p.count,
        pct: `${p.percentage}%`
      };
    });
    return map;
  }

  function renderTabs(profiles, rowCount, counts) {
    const tabsContainer = byId("segment-tabs");
    const clusterSelect = byId("cluster-select");
    if (!tabsContainer || !profiles) return;

    let tabsHTML = `<button class="px-4 py-2 border-b-2 border-primary text-primary font-label-sm text-label-sm font-semibold transition-all" data-segment="all">Tất cả · ${rowCount}</button>`;
    let selectHTML = `<option value="all">Tất cả phân khúc</option>`;

    profiles.forEach((p) => {
      const segId = p.cluster_id.toString();
      const cnt = counts[segId] !== undefined ? counts[segId] : p.count;
      tabsHTML += `<button class="px-4 py-2 border-b-2 border-transparent text-on-surface-variant hover:text-on-surface font-label-sm text-label-sm transition-all" data-segment="${segId}">${escapeHtml(p.cluster_label)} · ${cnt}</button>`;
      selectHTML += `<option value="${segId}">${escapeHtml(p.cluster_label)} (${cnt} KH)</option>`;
    });

    tabsContainer.innerHTML = tabsHTML;
    if (clusterSelect) clusterSelect.innerHTML = selectHTML;
  }

  function renderClusterCards(profiles) {
    const container = byId("cluster-cards-container");
    if (!container || !profiles) return;

    const k = profiles.length;
    let colClass = "col-span-12 lg:col-span-4";
    if (k === 2) colClass = "col-span-12 md:col-span-6";
    else if (k === 4) colClass = "col-span-12 md:col-span-6 lg:col-span-3";
    else if (k >= 5) colClass = "col-span-12 md:col-span-6 lg:col-span-4";

    container.innerHTML = profiles
      .map((p) => {
        const color = getColor(p.cluster_id);
        const cardId = `card-${p.cluster_id}`;
        return `
          <div class="${colClass} bg-surface-container-lowest rounded-xl border border-outline-variant p-md shadow-sm hover:shadow-md transition-all cursor-pointer relative overflow-hidden flex flex-col justify-between" data-card-segment="${p.cluster_id}" id="${cardId}">
            <div class="absolute top-0 right-0 p-2 opacity-10">
              <span class="material-symbols-outlined text-6xl" style="color: ${color}">group</span>
            </div>
            <div>
              <div class="flex justify-between items-start mb-sm relative z-10">
                <div class="flex items-center gap-sm">
                  <div class="w-4 h-4 rounded-full" style="background-color: ${color}"></div>
                  <h3 class="font-title-md text-title-md text-on-surface font-bold">${escapeHtml(p.cluster_label)}</h3>
                </div>
                <span class="font-label-sm text-label-sm bg-surface-container px-2 py-1 rounded text-on-surface-variant font-medium">${p.count} KH (${p.percentage}%)</span>
              </div>
              <div class="mb-md relative z-10">
                <div class="font-body-md text-body-md font-bold mb-1" style="color: ${color}">${escapeHtml(p.segment_name)}</div>
                <p class="font-label-sm text-label-sm text-on-surface-variant">Insight: ${escapeHtml(p.insight)}</p>
              </div>
            </div>
            <div class="grid grid-cols-3 gap-sm mt-auto pt-md border-t border-outline-variant relative z-10">
              <div>
                <div class="font-label-sm text-label-sm text-on-surface-variant">Mean R</div>
                <div class="font-body-md text-body-md font-semibold">${p.mean_recency}</div>
              </div>
              <div>
                <div class="font-label-sm text-label-sm text-on-surface-variant">Mean F</div>
                <div class="font-body-md text-body-md font-semibold">${p.mean_frequency}</div>
              </div>
              <div>
                <div class="font-label-sm text-label-sm text-on-surface-variant">Mean M</div>
                <div class="font-body-md text-body-md font-semibold">${p.mean_monetary}</div>
              </div>
            </div>
          </div>
        `;
      })
      .join("");
  }

  function renderComparisonCharts(profiles) {
    const container = byId("comparison-charts");
    if (!container || !profiles) return;

    const maxR = Math.max(...profiles.map((p) => p.mean_recency)) || 1.0;
    const maxF = Math.max(...profiles.map((p) => p.mean_frequency)) || 1.0;
    const maxM = Math.max(...profiles.map((p) => p.mean_monetary)) || 1.0;

    function buildMetricChart(title, sub, metricKey, maxVal) {
      let rowsHTML = profiles
        .map((p) => {
          const val = p[metricKey];
          const pct = Math.max(5, Math.min(100, Math.round((val / maxVal) * 100)));
          const color = getColor(p.cluster_id);
          const shortCode = `C${(p.cluster_id + 1).toString().padStart(2, "0")}`;
          return `
            <div class="flex items-center gap-2">
              <div class="w-8 text-right font-label-sm text-label-sm text-on-surface-variant font-medium">${shortCode}</div>
              <div class="flex-1 bg-surface-container h-4 rounded overflow-hidden flex">
                <div class="h-full rounded transition-all duration-500" style="width: ${pct}%; background-color: ${color}"></div>
              </div>
              <div class="w-16 text-left font-label-sm text-label-sm font-semibold">${val}</div>
            </div>
          `;
        })
        .join("");

      return `
        <div>
          <div class="flex justify-between font-label-sm text-label-sm mb-1">
            <span class="text-on-surface font-medium">${title}</span>
            <span class="text-on-surface-variant">${sub}</span>
          </div>
          <div class="flex flex-col gap-1.5">${rowsHTML}</div>
        </div>
      `;
    }

    container.innerHTML =
      buildMetricChart("Recency (Mean)", "Thấp hơn = mua gần đây hơn", "mean_recency", maxR) +
      buildMetricChart("Frequency (Mean)", "Cao hơn = mua thường xuyên hơn", "mean_frequency", maxF) +
      buildMetricChart("Monetary (Mean)", "Cao hơn = giá trị giao dịch lớn hơn", "mean_monetary", maxM);
  }

  function renderDetailPanel(segmentId, clusterInfo, profiles) {
    const profileTitle = byId("profile-title");
    const profileDesc = byId("profile-desc");
    if (!profileTitle || !profileDesc) return;

    if (segmentId === "all") {
      profileTitle.textContent = `Tổng quan ${profiles.length} phân khúc`;
      profileDesc.innerHTML = `<p class="font-body-md text-body-md text-on-surface-variant">Chọn một thẻ phân khúc bên trên hoặc dùng tab để xem hồ sơ RFM chi tiết của từng nhóm.</p>`;
    } else {
      const info = clusterInfo[segmentId];
      if (!info) return;
      profileTitle.textContent = `Hồ sơ ${info.label}`;
      profileDesc.innerHTML = `
        <div class="flex items-center gap-2 mb-1">
          <span class="inline-flex items-center justify-center px-2 py-0.5 rounded text-white font-label-sm text-label-sm font-medium" style="background-color: ${info.hex}">${escapeHtml(info.label)}</span>
        </div>
        <div class="font-body-lg font-bold mb-1" style="color: ${info.hex}">${escapeHtml(info.name)}</div>
        <div class="font-label-sm text-on-surface-variant mb-6">${info.total} khách hàng · ${info.pct} tổng dữ liệu</div>

        <div class="bg-surface-container-low p-4 rounded-xl border border-outline-variant mb-6">
          <div class="font-label-sm text-on-surface-variant uppercase tracking-wider mb-3 font-semibold">RFM Trung bình</div>
          <div class="grid grid-cols-3 gap-md">
            <div>
              <div class="font-label-sm text-on-surface-variant mb-1">Recency</div>
              <div class="font-title-md text-title-md font-bold text-on-surface">${info.means.r}</div>
            </div>
            <div>
              <div class="font-label-sm text-on-surface-variant mb-1">Frequency</div>
              <div class="font-title-md text-title-md font-bold text-on-surface">${info.means.f}</div>
            </div>
            <div>
              <div class="font-label-sm text-on-surface-variant mb-1">Monetary</div>
              <div class="font-title-md text-title-md font-bold text-on-surface">${info.means.m}</div>
            </div>
          </div>
        </div>

        <div class="font-label-sm text-on-surface-variant uppercase tracking-wider mb-1 font-semibold">✦ ĐẶC ĐIỂM NỔI BẬT</div>
        <div class="font-body-md text-body-md text-on-surface">${escapeHtml(info.desc)}</div>
      `;
    }
  }

  function renderTable() {
    if (!resultsData) return;
    const tbody = byId("customer-tbody");
    const tableCount = byId("table-count");
    if (!tbody) return;

    const customers = resultsData.customer_results || [];
    const clusterInfo = getClusterInfoMap(resultsData.cluster_profiles || []);

    const filtered = customers.filter((c) => {
      const matchCluster = currentFilter === "all" || c.cluster.toString() === currentFilter;
      const matchSearch = c.id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCluster && matchSearch;
    });

    const totalInFilter = resultsData.counts_and_percentages[currentFilter] || customers.length;
    const displayedCount = filtered.length;
    if (tableCount) {
      tableCount.textContent = `${totalInFilter} khách hàng · đang hiển thị ${displayedCount} dòng`;
    }

    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="py-12 text-center text-on-surface-variant">
            <div class="flex flex-col items-center justify-center">
              <span class="material-symbols-outlined text-4xl mb-2 opacity-50">search_off</span>
              <p class="font-body-md">Không tìm thấy CustomerID phù hợp.</p>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    // Render rows (limit DOM footprint if very large, but 720 rows render fast)
    tbody.innerHTML = filtered
      .map((c) => {
        const info = clusterInfo[c.cluster] || { hex: "#3525cd", name: c.name, label: `Cluster ${c.cluster}` };
        return `
          <tr class="border-b border-outline-variant hover:bg-surface-container-low transition-colors cursor-pointer group" data-customer-id="${escapeHtml(c.id)}">
            <td class="py-3 px-md font-medium text-on-surface flex items-center gap-2">
              ${escapeHtml(c.id)}
              <span class="material-symbols-outlined text-sm opacity-0 group-hover:opacity-100 transition-opacity" style="color: ${info.hex}">open_in_new</span>
            </td>
            <td class="py-3 px-md text-on-surface">${c.r}</td>
            <td class="py-3 px-md text-on-surface">${c.f}</td>
            <td class="py-3 px-md text-on-surface">${c.m}</td>
            <td class="py-3 px-md">
              <span class="inline-flex items-center justify-center w-6 h-6 rounded-full text-white text-xs font-bold" style="background-color: ${info.hex}">${c.cluster}</span>
            </td>
            <td class="py-3 px-md font-medium" style="color: ${info.hex}">${escapeHtml(c.name)}</td>
          </tr>
        `;
      })
      .join("");

    // Attach click handlers to open drawer
    tbody.querySelectorAll("tr").forEach((tr) => {
      const cid = tr.dataset.customerId;
      if (cid) {
        tr.addEventListener("click", () => {
          const cust = customers.find((x) => x.id === cid);
          if (cust) openDrawer(cust, clusterInfo);
        });
      }
    });
  }

  function openDrawer(customer, clusterInfo) {
    const drawer = byId("drawer");
    const drawerContent = byId("drawer-content");
    if (!drawer || !drawerContent) return;

    const info = clusterInfo[customer.cluster] || {
      hex: "#3525cd",
      label: `Cluster ${customer.cluster + 1}`,
      name: customer.name,
      means: { r: 50, f: 10, m: 1000 }
    };

    const rPct = Math.max(5, Math.min(100, Math.round((customer.r / (info.means.r * 2 || 1)) * 100)));
    const fPct = Math.max(5, Math.min(100, Math.round((customer.f / (info.means.f * 2 || 1)) * 100)));
    const mPct = Math.max(5, Math.min(100, Math.round((customer.m / (info.means.m * 2 || 1)) * 100)));

    drawerContent.innerHTML = `
      <div class="mb-6 flex items-center justify-between">
        <span class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface font-bold">${escapeHtml(customer.id)}</span>
        <span class="inline-flex items-center justify-center px-3 py-1 rounded-full text-white text-xs font-medium" style="background-color: ${info.hex}">${escapeHtml(info.label)} (Model ${customer.cluster})</span>
      </div>
      <p class="font-body-md mb-6 font-bold" style="color: ${info.hex}">${escapeHtml(customer.name)}</p>

      <div class="bg-surface-container-low p-4 rounded-xl border border-outline-variant mb-6">
        <h4 class="font-label-sm text-label-sm uppercase text-on-surface-variant mb-3 font-semibold">RFM KHÁCH HÀNG (GỐC)</h4>
        <div class="grid grid-cols-3 gap-2 text-center">
          <div>
            <div class="font-label-sm text-on-surface-variant mb-1">Recency</div>
            <div class="font-title-md font-bold text-on-surface">${customer.r}</div>
          </div>
          <div>
            <div class="font-label-sm text-on-surface-variant mb-1">Frequency</div>
            <div class="font-title-md font-bold text-on-surface">${customer.f}</div>
          </div>
          <div>
            <div class="font-label-sm text-on-surface-variant mb-1">Monetary</div>
            <div class="font-title-md font-bold text-on-surface">${customer.m}</div>
          </div>
        </div>
      </div>

      <h4 class="font-label-sm text-label-sm uppercase text-on-surface-variant mb-4 font-semibold">SO VỚI TRUNG BÌNH PHÂN KHÚC</h4>
      <div class="space-y-6">
        <div>
          <div class="flex justify-between items-center mb-2">
            <span class="font-label-sm text-label-sm text-on-surface-variant font-medium">Recency</span>
            <span class="font-body-md text-body-md text-on-surface"><strong>${customer.r}</strong> vs ${info.means.r}</span>
          </div>
          <div class="relative h-2 bg-surface-container rounded-full">
            <div class="absolute h-full bg-outline-variant rounded-full" style="width: ${rPct}%; left: 0;"></div>
            <div class="absolute h-4 w-4 rounded-full top-1/2 -translate-y-1/2 shadow" style="background-color: ${info.hex}; left: ${Math.min(95, rPct)}%;"></div>
          </div>
        </div>
        <div>
          <div class="flex justify-between items-center mb-2">
            <span class="font-label-sm text-label-sm text-on-surface-variant font-medium">Frequency</span>
            <span class="font-body-md text-body-md text-on-surface"><strong>${customer.f}</strong> vs ${info.means.f}</span>
          </div>
          <div class="relative h-2 bg-surface-container rounded-full">
            <div class="absolute h-full bg-outline-variant rounded-full" style="width: ${fPct}%; left: 0;"></div>
            <div class="absolute h-4 w-4 rounded-full top-1/2 -translate-y-1/2 shadow" style="background-color: ${info.hex}; left: ${Math.min(95, fPct)}%;"></div>
          </div>
        </div>
        <div>
          <div class="flex justify-between items-center mb-2">
            <span class="font-label-sm text-label-sm text-on-surface-variant font-medium">Monetary</span>
            <span class="font-body-md text-body-md text-on-surface"><strong>${customer.m}</strong> vs ${info.means.m}</span>
          </div>
          <div class="relative h-2 bg-surface-container rounded-full">
            <div class="absolute h-full bg-outline-variant rounded-full" style="width: ${mPct}%; left: 0;"></div>
            <div class="absolute h-4 w-4 rounded-full top-1/2 -translate-y-1/2 shadow" style="background-color: ${info.hex}; left: ${Math.min(95, mPct)}%;"></div>
          </div>
        </div>
      </div>
    `;
    drawer.classList.remove("translate-x-full");
  }

  function setFilter(segment) {
    currentFilter = segment;
    const clusterSelect = byId("cluster-select");
    if (clusterSelect) clusterSelect.value = segment;

    const segmentTabs = byId("segment-tabs");
    if (segmentTabs) {
      segmentTabs.querySelectorAll("button").forEach((btn) => {
        if (btn.dataset.segment === segment) {
          btn.className = "px-4 py-2 border-b-2 border-primary text-primary font-label-sm text-label-sm font-semibold transition-all";
        } else {
          btn.className = "px-4 py-2 border-b-2 border-transparent text-on-surface-variant hover:text-on-surface font-label-sm text-label-sm transition-all";
        }
      });
    }

    // Card styling
    const clusterInfo = getClusterInfoMap(resultsData.cluster_profiles || []);
    document.querySelectorAll("[data-card-segment]").forEach((card) => {
      const seg = card.dataset.cardSegment;
      const info = clusterInfo[seg];
      const selected = currentFilter === "all" || currentFilter === seg;
      if (selected && info) {
        card.classList.add("border-2");
        card.classList.remove("border");
        card.style.borderColor = info.hex;
      } else {
        card.classList.remove("border-2");
        card.classList.add("border");
        card.style.borderColor = "";
      }
    });

    renderDetailPanel(segment, clusterInfo, resultsData.cluster_profiles || []);
    renderTable();
  }

  function renderModelMetadata(data) {
    const meta = data.run_metadata || {};
    if (byId("meta-k")) byId("meta-k").textContent = meta.k;
    if (byId("meta-init")) byId("meta-init").textContent = meta.init;
    if (byId("meta-ninit")) byId("meta-ninit").textContent = meta.n_init;
    if (byId("meta-rs")) byId("meta-rs").textContent = meta.random_state;
    if (byId("meta-maxiter")) byId("meta-maxiter").textContent = meta.max_iter;
    if (byId("meta-tol")) byId("meta-tol").textContent = meta.tol;
    if (byId("meta-inertia")) byId("meta-inertia").textContent = Number(meta.inertia).toFixed(4);
    if (byId("meta-silhouette")) byId("meta-silhouette").textContent = Number(meta.silhouette).toFixed(4);
    if (byId("meta-iterations")) byId("meta-iterations").textContent = meta.iterations;
    if (byId("meta-runtime")) byId("meta-runtime").textContent = `${Number(meta.runtime_seconds).toFixed(2)} s`;

    if (byId("chk-customers")) {
      byId("chk-customers").textContent = `${data.row_count}/${data.row_count} khách hàng đã được phân cụm thành công`;
    }
  }

  function renderResults(data) {
    resultsData = data;
    const profiles = data.cluster_profiles || [];
    const rowCount = data.row_count ?? 0;
    const counts = data.counts_and_percentages || {};

    // Header badge
    const badge = byId("header-status-badge");
    if (badge) {
      badge.textContent = `Phân tích hoàn tất | ${rowCount} khách hàng · ${data.selected_k} phân khúc`;
    }

    renderTabs(profiles, rowCount, counts);
    renderClusterCards(profiles);
    renderComparisonCharts(profiles);
    renderModelMetadata(data);
    if (window.renderWorkflowProgress) window.renderWorkflowProgress(data);

    // Initial filter state
    setFilter("all");

    // Events
    const segmentTabs = byId("segment-tabs");
    if (segmentTabs) {
      segmentTabs.addEventListener("click", (e) => {
        if (e.target.tagName === "BUTTON") {
          setFilter(e.target.dataset.segment);
        }
      });
    }

    const clusterSelect = byId("cluster-select");
    if (clusterSelect) {
      clusterSelect.addEventListener("change", (e) => {
        setFilter(e.target.value);
      });
    }

    document.querySelectorAll("[data-card-segment]").forEach((card) => {
      card.addEventListener("click", () => {
        setFilter(card.dataset.cardSegment);
      });
    });

    const searchInput = byId("customer-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value;
        renderTable();
      });
    }

    const closeDrawerBtn = byId("close-drawer");
    if (closeDrawerBtn) {
      closeDrawerBtn.addEventListener("click", () => {
        const drawer = byId("drawer");
        if (drawer) drawer.classList.add("translate-x-full");
      });
    }
  }

  // Load from API
  fetch("/api/results")
    .then((res) => {
      if (!res.ok) {
        window.location.href = "/clustering";
        return null;
      }
      return res.json();
    })
    .then((data) => {
      if (data) renderResults(data);
    })
    .catch((err) => {
      console.error("Error loading /api/results:", err);
      window.location.href = "/clustering";
    });
})();
