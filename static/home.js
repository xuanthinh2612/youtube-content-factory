(() => {
  const form = document.querySelector("[data-generation-form]");
  if (!form) return;

  const languageChoices = [...form.querySelectorAll("input[type=checkbox]")].filter((input) => input.closest("[data-language-option]"));
  const languageInputs = form.querySelector("[data-language-inputs]");
  const languageCount = form.querySelector("[data-language-count]");
  const search = form.querySelector("[data-language-search]");
  const duration = form.querySelector('input[name="duration_minutes"]');
  const durationValue = form.querySelector("[data-duration-value]");
  const durationMaxLabel = form.querySelector("[data-duration-max]");
  const nicheInputs = [...form.querySelectorAll('input[name="niche"]')];

  function updateDurationLimit() {
    if (!duration) return;
    const max = form.querySelector('input[name="niche"]:checked')?.value === "music" ? 8 : 60;
    duration.max = String(max);
    if (Number(duration.value) > max) duration.value = String(max);
    if (durationValue) durationValue.value = duration.value;
    if (durationMaxLabel) durationMaxLabel.textContent = max + " phút";
  }

  duration?.addEventListener("input", () => {
    if (durationValue) durationValue.value = duration.value;
  });
  nicheInputs.forEach((input) => input.addEventListener("change", updateDurationLimit));
  updateDurationLimit();

  function updateLanguageCount() {
    if (!languageCount) return;
    const selectedLanguages = languageChoices.filter((input) => input.checked).map((input) => input.value);
    const selected = selectedLanguages.length;
    if (languageInputs) {
      languageInputs.replaceChildren(...selectedLanguages.map((language) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "languages";
        input.value = language;
        return input;
      }));
    }
    languageCount.textContent = selected
      ? `Đã chọn ${selected} ngôn ngữ`
      : "Chưa chọn ngôn ngữ nào";
  }

  languageChoices.forEach((input) => input.addEventListener("change", updateLanguageCount));
  updateLanguageCount();

  search?.addEventListener("input", () => {
    const query = search.value.trim().toLocaleLowerCase();
    form.querySelectorAll("[data-language-option]").forEach((option) => {
      option.hidden = !option.dataset.languageName.includes(query);
    });
  });
})();
