(() => {
  const projectId = document.body.dataset.projectId;
  const connection = document.querySelector("[data-connection-state]");
  if (!projectId || !connection) return;

  document.querySelectorAll("form[data-confirm-delete]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirmDelete)) event.preventDefault();
    });
  });

  document.querySelectorAll(".input-expandable").forEach((section) => {
    const toggle = section.querySelector(".input-toggle");
    section.addEventListener("toggle", () => {
      toggle.textContent = section.open ? "Thu gọn" : "Mở rộng";
    });
  });

  const eventsList = document.querySelector("[data-project-events]");

  function setupEventContent(item) {
    const message = item.querySelector(".event-content");
    if (!message) return;

    let toggle = item.querySelector("[data-event-content-toggle]");
    if (!toggle) {
      toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "event-content-toggle";
      toggle.dataset.eventContentToggle = "";
      toggle.textContent = "Xem thêm";
      toggle.setAttribute("aria-expanded", "false");
      toggle.addEventListener("click", () => {
        const expanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!expanded));
        toggle.textContent = expanded ? "Xem thêm" : "Thu gọn";
        message.classList.toggle("is-collapsed", expanded);
      });
      message.after(toggle);
    }

    if (toggle.getAttribute("aria-expanded") === "true") return;
    message.classList.add("is-collapsed");
    toggle.hidden = message.scrollHeight <= message.clientHeight + 1;
  }

  eventsList.querySelectorAll("[data-event-id]").forEach(setupEventContent);
  window.addEventListener("resize", () => {
    eventsList.querySelectorAll("[data-event-id]").forEach(setupEventContent);
  });
  const seenEvents = new Set(
    [...eventsList.querySelectorAll("[data-event-id]")].map((item) => item.dataset.eventId),
  );
  const terminalStatuses = new Set(["completed", "failed", "cancelled"]);
  const agentStates = new Map();
  let socket;
  let retryDelay = 1000;
  let terminal = false;

  function setAgent(name, status, message) {
    const row = document.querySelector(`[data-agent-state="${CSS.escape(name)}"]`);
    if (!row) return;
    const badge = row.querySelector("[data-agent-status]");
    badge.textContent = status;
    badge.className = `status ${status}`;
    if (message) row.querySelector("[data-agent-message]").textContent = message;
  }

  function addEvent(event) {
    if (event.id === undefined || seenEvents.has(String(event.id))) return;
    seenEvents.add(String(event.id));
    eventsList.querySelector("[data-event-empty]")?.remove();

    const item = document.createElement("li");
    item.dataset.eventId = String(event.id);
    const heading = document.createElement("div");
    const name = document.createElement("strong");
    const agentName = event.node;
    const labels = { director: "Director", writer: "Writer", reviewer: "Reviewer", editor: "Editor" };
    name.textContent = `${labels[agentName] || agentName || event.type || "Event"}${event.language ? ` · ${event.language_name || event.language}` : ""}`;
    const time = document.createElement("time");
    time.textContent = event.ts ? new Date(event.ts).toLocaleString() : "";
    heading.append(name, time);
    item.append(heading);
    if (event.message_html) {
      const message = document.createElement("article");
      message.className = "event-content markdown is-collapsed";
      message.innerHTML = event.message_html;
      item.append(message);
    } else if (event.message) {
      const message = document.createElement("p");
      message.className = "event-content plain";
      message.textContent = event.message;
      item.append(message);
    }
    eventsList.prepend(item);
    setupEventContent(item);

    const state = agentStates.get(agentName) || { status: "idle", message: "" };
    if (event.type === "node_success") state.status = "success";
    else if (event.type === "node_error") state.status = "failed";
    else if (event.type === "step" && ["running", "success", "failed"].includes(event.status)) {
      state.status = event.status;
    }
    state.message = event.type === "node_success" ? "Output ready" : event.message || state.message;
    agentStates.set(agentName, state);
    if (agentName) setAgent(agentName, state.status, state.message);
  }

  function receiveUpdate(update) {
    if (update.type !== "project_update" || !update.project) return;
    const project = update.project;
    const badge = document.querySelector("[data-project-status]");
    badge.textContent = project.status;
    badge.className = `status ${project.status}`;
    document.querySelector("[data-project-stage]").textContent = project.stage;
    document.querySelector("[data-project-progress-label]").textContent = `${project.progress}%`;
    document.querySelector("[data-project-progress]").value = project.progress;
    if (["director", "writer", "reviewer", "editor"].includes(project.stage) && project.status === "running") {
      setAgent(project.stage, "running");
    }

    const errorBox = document.querySelector("[data-project-error]");
    errorBox.hidden = !project.error;
    document.querySelector("[data-project-error-message]").textContent = project.error || "";
    for (const event of update.events || []) addEvent(event);

    terminal = terminalStatuses.has(project.status);
    if (terminal) {
      document.querySelector("[data-stop-form]")?.remove();
      connection.textContent = "Đã nhận trạng thái cuối cùng";
      socket?.close();
    }
  }

  function connect() {
    if (terminal) return;
    const scheme = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${scheme}//${location.host}/ws/projects/${encodeURIComponent(projectId)}`);
    socket.onopen = () => {
      retryDelay = 1000;
      connection.textContent = "Realtime đang kết nối";
    };
    socket.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data);
        if (payload.type === "pong") return;
        receiveUpdate(payload);
      } catch {
        connection.textContent = "Không đọc được cập nhật realtime";
      }
    };
    socket.onerror = () => {
      connection.textContent = "Mất kết nối realtime, đang thử lại";
    };
    socket.onclose = () => {
      if (terminal) return;
      connection.textContent = "Đang kết nối lại…";
      window.setTimeout(connect, retryDelay);
      retryDelay = Math.min(retryDelay * 2, 10000);
    };
  }

  window.setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) socket.send('{"type":"ping"}');
  }, 20000);
  connect();
})();
