import { useEffect, useState } from "react";

const THEMES = ["dark", "midnight", "glass", "light", "graphite"];

export function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem("jx-jarvis-theme") || "dark");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("jx-jarvis-theme", theme);
  }, [theme]);

  return { theme, setTheme, themes: THEMES };
}
