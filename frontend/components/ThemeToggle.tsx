"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-9 h-9 rounded-lg bg-surface-card border border-border animate-pulse" />
    );
  }

  return (
    <button
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      className="p-2 rounded-lg bg-surface-card border border-border text-txt-secondary hover:text-txt-primary hover:border-brand-primary transition-all duration-200 flex items-center justify-center"
      aria-label="Toggle Theme"
      title={theme === "light" ? "Switch to Midnight Finance Dark Mode" : "Switch to Clean Market Light Mode"}
    >
      {theme === "light" ? (
        <Moon className="w-4 h-4 text-brand-primary" />
      ) : (
        <Sun className="w-4 h-4 text-warning" />
      )}
    </button>
  );
}
