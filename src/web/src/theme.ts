export type Theme = "light" | "dark";

const THEME_STORAGE = "folha-ponto-theme";

export function getInitialTheme(): Theme {
  const stored = localStorage.getItem(THEME_STORAGE);
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
}

export function storeTheme(theme: Theme): void {
  localStorage.setItem(THEME_STORAGE, theme);
}
