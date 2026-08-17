(function () {
  "use strict";
  const byId = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value ?? "—").replace(/[&<>'"]/g, (character) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[character]);
  function renderDatasetState(state) {
    window.renderWorkflowProgress(state);
    const panel = byId("dataset-status");
    const btnToEda = byId("btn-to-eda");
    if (!state.dataset_loaded) {
      panel.classList.add("hidden");
      if (btnToEda) {
        btnToEda.classList.add("opacity-60", "pointer-events-none");
        btnToEda.setAttribute("tabindex", "-1");
      }
      return;
    }
    panel.classList.remove("hidden");
    if (btnToEda) {
      btnToEda.classList.remove("opacity-60", "pointer-events-none");
      btnToEda.removeAttribute("tabindex");
    }
    byId("dataset-row-count").textContent = state.row_count;
    byId("dataset-signature").textContent = state.dataset_signature;
    const quality = state.quality_report;
    const columns = ["Recency", "Frequency", "Monetary"];
    const missing = Object.values(quality.missing_by_column).reduce((sum, value) => sum + value, 0);
    const outliers = Object.values(quality.iqr_outlier_by_column).reduce((sum, value) => sum + value, 0);
    byId("missing-total").textContent = missing; byId("outlier-total").textContent = outliers;
    byId("guidance-missing").textContent = missing ? `⚠ ${missing} giá trị RFM còn thiếu` : "✓ Không có giá trị RFM còn thiếu";
    byId("guidance-outliers").textContent = outliers ? `⚠ ${outliers} giá trị ngoại lệ theo IQR` : "✓ Không có giá trị ngoại lệ theo IQR";
    byId("quality-body").innerHTML = columns.map((column) => {
      const missingCount = quality.missing_by_column[column], outlierCount = quality.iqr_outlier_by_column[column];
      return `<tr><td class="py-3 px-4 font-medium text-on-surface">${column}</td><td class="py-3 px-4 text-on-surface-variant">${missingCount} (${(missingCount*100/quality.row_count).toFixed(1)}%)</td><td class="py-3 px-4 text-amber-600 font-medium">${outlierCount} (${(outlierCount*100/quality.row_count).toFixed(1)}%)</td><td class="py-3 px-4"><span class="material-symbols-outlined text-secondary text-[20px]">check_circle</span></td></tr>`;
    }).join("");
    byId("preview-body").innerHTML = state.preview.map((row,index) => `<tr class="hover:bg-surface-container-lowest transition-colors"><td class="py-3 px-6 text-on-surface-variant">${index+1}</td><td class="py-3 px-6 font-medium text-on-surface">${escapeHtml(row.CustomerID)}</td><td class="py-3 px-6 text-right text-on-surface-variant">${escapeHtml(row.Recency)}</td><td class="py-3 px-6 text-right text-on-surface-variant">${escapeHtml(row.Frequency)}</td><td class="py-3 px-6 text-right text-on-surface-variant">${escapeHtml(row.Monetary)}</td></tr>`).join("");
  }
  async function sendDataset(url, options) {
    const error = byId("dataset-error"); error.classList.add("hidden");
    try { const response = await fetch(url, options), state = await response.json(); if (!response.ok) throw new Error(state.detail || "Không thể xử lý dữ liệu."); renderDatasetState(state); byId("dataset-status").scrollIntoView({behavior:"smooth",block:"start"}); }
    catch (failure) { error.textContent = failure.message; error.classList.remove("hidden"); }
  }
  function upload(file) { if (!file) return; const form = new FormData(); form.append("file",file); sendDataset("/api/dataset/upload",{method:"POST",body:form}); }
  window.renderDatasetState = renderDatasetState;
  const input=byId("csv-file"), dropzone=byId("dropzone");
  byId("sample-button").addEventListener("click",()=>sendDataset("/api/dataset/sample",{method:"POST"}));
  byId("choose-file").addEventListener("click",(event)=>{event.stopPropagation();input.click();});
  dropzone.addEventListener("click",()=>input.click()); input.addEventListener("change",()=>upload(input.files[0]));
  ["dragenter","dragover"].forEach((name)=>dropzone.addEventListener(name,(event)=>{event.preventDefault();dropzone.classList.add("border-primary","bg-surface-container-low");}));
  ["dragleave","drop"].forEach((name)=>dropzone.addEventListener(name,(event)=>{event.preventDefault();dropzone.classList.remove("border-primary","bg-surface-container-low");}));
  dropzone.addEventListener("drop",(event)=>upload(event.dataTransfer.files[0]));
})();
