/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "var(--border)",
        input: "var(--border)",
        ring: "var(--brand-primary)",
        background: "var(--bg-main)",
        foreground: "var(--text-primary)",

        // Midnight Finance Custom Tokens
        brand: {
          primary: "var(--brand-primary)",
          bright: "var(--brand-bright)",
          deep: "var(--brand-deep)",
        },
        surface: {
          main: "var(--bg-main)",
          secondary: "var(--bg-secondary)",
          card: "var(--bg-card)",
          elevated: "var(--bg-elevated)",
        },
        financial: {
          profit: "var(--profit)",
          profitLight: "var(--profit-light)",
          loss: "var(--loss)",
          lossLight: "var(--loss-light)",
          warning: "var(--warning)",
          info: "var(--info)",
        },
        ai: {
          violet: "var(--ai-violet)",
          light: "var(--ai-light)",
        },
        txt: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
        },
      },
      borderRadius: {
        lg: "0.75rem",
        md: "0.5rem",
        sm: "0.25rem",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Courier New", "monospace"],
      },
    },
  },
  plugins: [],
};
