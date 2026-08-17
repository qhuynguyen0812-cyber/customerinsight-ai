(function () {
  "use strict";

  function renderProgress(state) {
    if (!state) return;
    const progress = state.workflow_progress || {
      completed_steps: 0,
      total_steps: 5,
      percent: 0,
      next_step: "Dữ liệu"
    };

    const bar = document.getElementById("workflow-progress-bar");
    const count = document.getElementById("workflow-progress-count");
    const pct = document.getElementById("workflow-progress-pct");
    const next = document.getElementById("workflow-progress-next");

    if (bar) bar.style.width = `${progress.percent}%`;
    if (pct) pct.textContent = `${progress.percent}%`;
    if (count) {
      if (count.textContent && count.textContent.includes("bước hoàn tất")) {
        count.textContent = `${progress.completed_steps} / ${progress.total_steps} bước hoàn tất`;
      } else {
        count.textContent = `${progress.completed_steps} / ${progress.total_steps} bước hoàn tất`;
      }
    }
    if (next) {
      if (progress.completed_steps >= 5 || progress.next_step === "Phân tích hoàn tất" || progress.percent >= 100) {
        next.className = "font-label-sm text-[10px] text-primary font-semibold mt-2 border-t border-outline-variant/30 pt-2 flex items-center gap-1";
        next.innerHTML = `<span class="material-symbols-outlined text-xs" style="font-size: 14px; font-variation-settings: 'FILL' 1;">check_circle</span> Phân tích hoàn tất`;
      } else {
        next.className = "font-label-sm text-[10px] text-on-surface-variant mt-2 border-t border-outline-variant/30 pt-2";
        next.textContent = `Tiếp theo: ${progress.next_step}`;
      }
    }
  }

  window.renderWorkflowProgress = renderProgress;

  document.querySelectorAll("[data-disabled]").forEach((link) => {
    link.setAttribute("aria-disabled", "true");
    link.title = "Đang được chuyển đổi";
    link.addEventListener("click", (event) => event.preventDefault());
  });

  fetch("/api/state")
    .then((response) => response.json())
    .then((state) => {
      renderProgress(state);
      if (window.renderDatasetState) window.renderDatasetState(state);
    })
    .catch((err) => console.error("Error loading initial state in app.js:", err));
})();
