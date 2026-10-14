import { useEffect, useState } from "react";

type Theme = "system" | "light" | "dark";

const STORAGE_KEY = "ss-theme";

/** What index.html stored before first paint, if anything. */
function storedTheme(): Theme {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system";
  }
}

/**
 * Light / dark / follow-the-system switch.
 *
 * "system" removes the attribute entirely so the stylesheet's
 * prefers-color-scheme rule decides; the other two pin it. The choice is
 * written to localStorage, which index.html reads before first paint to
 * avoid a flash of the wrong theme.
 */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(storedTheme);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", theme);
    }
    try {
      if (theme === "system") localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* storage blocked: the attribute still applies for this session */
    }
  }, [theme]);

  const options: { value: Theme; label: string }[] = [
    { value: "light", label: "Light" },
    { value: "system", label: "Auto" },
    { value: "dark", label: "Dark" },
  ];

  return (
    <div className="theme-toggle" role="group" aria-label="Colour theme">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className={option.value === theme ? "active" : undefined}
          aria-pressed={option.value === theme}
          onClick={() => setTheme(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
