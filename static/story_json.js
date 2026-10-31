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

  async function showResult({ response, payload, errorBox, result, name, path, download, preview }) {
    if (!response.ok) throw new Error(payload.detail || "Không thể tạo file JSON.");
    name.textContent = `${payload.project_name || payload.story_name} · ${payload.filename}`;
    path.textContent = `Đã lưu tại ${payload.path}`;
    download.href = payload.download_url;
    download.download = payload.filename;
    preview.textContent = "Đang tải bản xem trước…";
    result.hidden = false;
    try {
      const fileResponse = await fetch(payload.download_url);
      if (!fileResponse.ok) throw new Error("Không tải được bản xem trước.");
      preview.textContent = JSON.stringify(JSON.parse(await fileResponse.text()), null, 2);
    } catch {
      preview.textContent = "File đã được lưu. Dùng nút Tải file JSON để mở nội dung.";
    }
  }

  function setupFileImport(form, textarea) {
    const button = form.querySelector("[data-import-button]");
    const fileInput = form.querySelector("[data-import-file]");
    const status = form.querySelector("[data-import-status]");
    const submit = form.querySelector('button[type="submit"]');
    button.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", async () => {
      const file = fileInput.files?.[0];
      if (!file) return;
      button.disabled = true;
      submit.disabled = true;
      fileInput.disabled = true;
      textarea.disabled = true;
      status.textContent = `Đang đọc ${file.name}…`;
      try {
        textarea.value = await file.text();
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
        status.textContent = `Đã nhập ${file.name}`;
        textarea.focus();
      } catch {
        status.textContent = `Không đọc được file ${file.name}.`;
      } finally {
        textarea.disabled = false;
        button.disabled = false;
        submit.disabled = false;
        fileInput.disabled = false;
        fileInput.value = "";
      }
    });
  }

  const audioForm = app.querySelector("[data-audio-form]");
  setupFileImport(audioForm, audioForm.elements.story);
  audioForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = app.querySelector("[data-audio-submit]");
    const textarea = audioForm.elements.story;
    const importButton = audioForm.querySelector("[data-import-button]");
    const fileInput = audioForm.querySelector("[data-import-file]");
    const errorBox = app.querySelector("[data-audio-error]");
    const result = app.querySelector("[data-audio-result]");
    errorBox.hidden = true;
    result.hidden = true;
    submit.disabled = true;
    textarea.disabled = true;
    importButton.disabled = true;
    fileInput.disabled = true;
    submit.textContent = "Đang tạo JSON…";
    try {
      const response = await fetch("/api/story-audio-json", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story: audioForm.elements.story.value }),
      });
      const payload = await response.json().catch(() => ({}));
      await showResult({
        response, payload, errorBox, result,
        name: app.querySelector("[data-audio-result-name]"),
        path: app.querySelector("[data-audio-result-path]"),
        download: app.querySelector("[data-audio-download]"),
        preview: app.querySelector("[data-audio-preview]"),
      });
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
    } finally {
      submit.disabled = false;
      textarea.disabled = false;
      importButton.disabled = false;
      fileInput.disabled = false;
      submit.textContent = "Tạo JSON audio";
    }
  });

  app.querySelectorAll("[data-project-form]").forEach((form) => {
    setupFileImport(form, form.elements.content);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const projectType = form.dataset.projectType;
      const submit = form.querySelector("[data-project-submit]");
      const textarea = form.elements.content;
      const importButton = form.querySelector("[data-import-button]");
      const fileInput = form.querySelector("[data-import-file]");
      const panel = form.closest("[data-panel]");
      const errorBox = panel.querySelector("[data-project-error]");
      const result = panel.querySelector("[data-project-result]");
      errorBox.hidden = true;
      result.hidden = true;
      submit.disabled = true;
      textarea.disabled = true;
      importButton.disabled = true;
      fileInput.disabled = true;
      submit.textContent = `Đang tạo JSON ${projectType}…`;
      try {
        const response = await fetch("/api/story-project-json", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_type: projectType, content: form.elements.content.value }),
        });
        const payload = await response.json().catch(() => ({}));
        await showResult({
          response, payload, errorBox, result,
          name: panel.querySelector("[data-project-result-name]"),
          path: panel.querySelector("[data-project-result-path]"),
          download: panel.querySelector("[data-project-download]"),
          preview: panel.querySelector("[data-project-preview]"),
        });
      } catch (error) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
      } finally {
        submit.disabled = false;
        textarea.disabled = false;
        importButton.disabled = false;
        fileInput.disabled = false;
        submit.textContent = `Tạo JSON ${projectType}`;
      }
    });
  });
})();
