import { createContext, useContext, useLayoutEffect, useMemo } from "react";

type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
};

const ThemeCtx = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }): React.ReactElement {
  useLayoutEffect(() => {
    if (typeof document !== "undefined") {
      const root = document.documentElement;
      root.classList.add("dark");
      root.setAttribute("data-theme", "dark");
    }
  }, []);

  const value = useMemo(
    () => ({
      theme: "dark" as Theme,
      toggleTheme: () => {
        // Theme is fixed to dark; toggle is intentionally inert.
      },
    }),
    [],
  );

  return <ThemeCtx.Provider value={value}>{children}</ThemeCtx.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeCtx);
  if (!ctx) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return ctx;
}
