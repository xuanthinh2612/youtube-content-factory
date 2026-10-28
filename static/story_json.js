(() => {
  const app = document.querySelector("[data-story-json-app]");
  if (!app) return;

  const tabs = [...app.querySelectorAll("[data-tab]")];
  const panels = [...app.querySelectorAll("[data-panel]")];
  tabs.forEach((tab) => tab.addEventListener("click", () => {
    tabs.forEach((item) => {
      const selected = item === tab;
      item.classList.toggle("active", selected);
      item.setAttribute("aria-selected", String(selected));
    });
    panels.forEach((panel) => { panel.hidden = panel.dataset.panel !== tab.dataset.tab; });
  }));

  const form = app.querySelector("[data-story-json-form]");
  const submit = app.querySelector("[data-submit]");
  const errorBox = app.querySelector("[data-error]");
  const result = app.querySelector("[data-result]");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.hidden = true;
    result.hidden = true;
    submit.disabled = true;
    submit.textContent = "Đang tạo JSON…";
    try {
      const response = await fetch("/api/story-audio-json", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story: form.elements.story.value }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Không thể tạo file JSON.");
      app.querySelector("[data-result-name]").textContent = `${payload.story_name} · ${payload.filename}`;
      app.querySelector("[data-result-path]").textContent = `Đã lưu tại ${payload.path}`;
      const download = app.querySelector("[data-download]");
      download.href = payload.download_url;
      const preview = app.querySelector("[data-json-preview]");
      preview.textContent = "Đang tải bản xem trước…";
      result.hidden = false;
      try {
        const fileResponse = await fetch(payload.download_url);
        if (!fileResponse.ok) throw new Error("Không tải được bản xem trước.");
        const jsonText = await fileResponse.text();
        preview.textContent = JSON.stringify(JSON.parse(jsonText), null, 2);
      } catch {
        preview.textContent = "File đã được lưu. Dùng nút Tải file JSON để mở nội dung.";
      }
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
    } finally {
      submit.disabled = false;
      submit.textContent = "Tạo JSON audio";
    }
  });
})();
