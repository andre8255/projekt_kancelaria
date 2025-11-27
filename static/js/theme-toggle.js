(function () {
  const STORAGE_KEY = "kp-theme";

  function applyTheme(theme) {
    const html = document.documentElement;
    const next = theme === "dark" ? "dark" : "light";
    html.setAttribute("data-theme", next);

    const icon = document.getElementById("theme-toggle-icon");
    if (icon) {
      // jeśli używasz Bootstrap Icons
      if (icon.classList.contains("bi")) {
        icon.classList.remove("bi-moon-stars", "bi-sun");
        icon.classList.add(next === "dark" ? "bi-sun" : "bi-moon-stars");
      } else {
        // fallback dla zwykłego <span> z emoji
        icon.textContent = next === "dark" ? "☀️" : "🌙";
      }
    }
  }

  // wybór startowy: z localStorage albo z ustawień systemu
  const saved = localStorage.getItem(STORAGE_KEY);
  const prefersDark =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;

  const initial = saved || (prefersDark ? "dark" : "light");
  applyTheme(initial);

  const btn = document.getElementById("theme-toggle");
  if (!btn) return;

  btn.addEventListener("click", function () {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    applyTheme(next);
    localStorage.setItem(STORAGE_KEY, next);
  });
})();
