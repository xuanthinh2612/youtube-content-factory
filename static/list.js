(() => {
  const rows = new Map(
    [...document.querySelectorAll("[data-project-row]")].map((row) => [row.dataset.projectRow, row]),
  );
  let socket;
  let retryDelay = 1000;
  const selectionInputs = [...document.querySelectorAll(".project-select")];
  const selectAll = document.querySelector("[data-select-all]");
  const selectionCount = document.querySelector("[data-selection-count]");
  const bulkDelete = document.querySelector("[data-bulk-delete]");

  function updateSelection() {
    const selectedCount = selectionInputs.filter((input) => input.checked).length;
    if (selectAll) {
      selectAll.checked = selectionInputs.length > 0 && selectedCount === selectionInputs.length;
      selectAll.indeterminate = selectedCount > 0 && selectedCount < selectionInputs.length;
    }
    if (selectionCount) selectionCount.textContent = `Đã chọn ${selectedCount} project`;
    if (bulkDelete) bulkDelete.disabled = selectedCount === 0;
    for (const input of selectionInputs) input.closest("tr")?.classList.toggle("selected", input.checked);
  }

  selectAll?.addEventListener("change", () => {
    for (const input of selectionInputs) input.checked = selectAll.checked;
    updateSelection();
  });
  for (const input of selectionInputs) input.addEventListener("change", updateSelection);

  document.querySelector("#bulk-delete")?.addEventListener("submit", (event) => {
    const selectedCount = selectionInputs.filter((input) => input.checked).length;
    if (!selectedCount || !window.confirm(`Xóa ${selectedCount} project đã chọn? Thao tác này không thể hoàn tác.`)) {
      event.preventDefault();
    }
  });
  document.querySelectorAll("form[data-confirm-delete]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirmDelete)) event.preventDefault();
    });
  });
  updateSelection();

  function applyUpdate(update) {
    if (update.type !== "projects_update" || !Array.isArray(update.projects)) return;
    if (update.projects.length !== rows.size || update.projects.some((project) => !rows.has(project.id))) {
      location.reload();
      return;
    }
    for (const project of update.projects) {
      const row = rows.get(project.id);
      row.querySelector("[data-project-name]").textContent = project.name;
      const status = row.querySelector("[data-project-status]");
      status.textContent = project.status;
      status.className = `status ${project.status}`;
      row.querySelector("[data-project-progress]").value = project.progress;
      row.querySelector("[data-project-progress-label]").textContent = `${project.progress}%`;
      row.querySelector("[data-project-stage]").textContent = project.stage;
    }
  }

  function connect() {
    const scheme = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${scheme}//${location.host}/ws/projects`);
    socket.onopen = () => { retryDelay = 1000; };
    socket.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data);
        if (payload.type !== "pong") applyUpdate(payload);
      } catch {
        // Ignore a malformed frame and keep the status connection alive.
      }
    };
    socket.onclose = () => {
      window.setTimeout(connect, retryDelay);
      retryDelay = Math.min(retryDelay * 2, 10000);
    };
  }

  window.setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) socket.send('{"type":"ping"}');
  }, 20000);
  connect();
})();
