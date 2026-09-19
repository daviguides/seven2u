/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--c-bg) / <alpha-value>)",
        surface: "rgb(var(--c-surface) / <alpha-value>)",
        elevated: "rgb(var(--c-elevated) / <alpha-value>)",
        primary: "rgb(var(--c-primary) / <alpha-value>)",
        "primary-hover": "rgb(var(--c-primary-hover) / <alpha-value>)",
        accent: "rgb(var(--c-accent) / <alpha-value>)",
        "text-primary": "rgb(var(--c-text) / <alpha-value>)",
        "text-secondary": "rgb(var(--c-text-2) / <alpha-value>)",
        "text-muted": "rgb(var(--c-text-3) / <alpha-value>)",
        success: "rgb(var(--c-success) / <alpha-value>)",
        border: "rgb(var(--c-border) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "12px",
        btn: "8px",
        chip: "6px",
        poster: "8px",
      },
      transitionDuration: {
        DEFAULT: "150ms",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
