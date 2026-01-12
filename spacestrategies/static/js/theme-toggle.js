(function () {
  const STORAGE_KEY = "theme"; // "light" | "dark"
  const root = document.documentElement;

  function set(theme) {
    if (theme === "dark") root.setAttribute("data-theme", "dark");
    else root.removeAttribute("data-theme");
  }

  // init: saved preference, otherwise system preference
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "dark" || saved === "light") {
    set(saved);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    set("dark");
  }

  window.toggleTheme = function () {
    const isDark = root.getAttribute("data-theme") === "dark";
    const next = isDark ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, next);
    set(next);
  };
})();
