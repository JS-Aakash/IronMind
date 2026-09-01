import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        border: "var(--border)",
        obsidian: {
          950: "#06080c",
          900: "#0b0f17",
          850: "#101622",
          800: "#172030",
          700: "#223049",
          600: "#324466",
          500: "#48628f",
          400: "#6986ba",
          300: "#95aee0",
          200: "#c4d4f4",
          100: "#e5edf9",
          50: "#f4f7fc",
        },
        industrial: {
          950: "#06080c",
          900: "#0b0f17",
          850: "#101622",
          800: "#172030",
          700: "#223049",
          600: "#324466",
          500: "#48628f",
          400: "#6986ba",
          300: "#95aee0",
          200: "#c4d4f4",
          100: "#e5edf9",
          50: "#f4f7fc",
        },
        accent: {
          indigo: "#6366f1",
          violet: "#8b5cf6",
          cyan: "#06b6d4",
          sky: "#0ea5e9",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "-apple-system", "BlinkMacSystemFont", "'Segoe UI'", "Roboto", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        glow: {
          "0%": { filter: "drop-shadow(0 0 8px rgba(99, 102, 241, 0.4))" },
          "100%": { filter: "drop-shadow(0 0 18px rgba(6, 182, 212, 0.7))" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
