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
        // Enterprise Industrial Palette
        iron: {
          bg: "#0A0F1C",
          panel: "#101827",
          panelSecondary: "#151E30",
          border: "#26344D",
          borderLight: "rgba(78, 161, 255, 0.18)",
          textPrimary: "#F5F7FB",
          textSecondary: "#9AA7BC",
          accentPrimary: "#4EA1FF",
          accentSecondary: "#6C63FF",
          success: "#35D07F",
          warning: "#F2B84B",
          error: "#FF5C67",
        },
        // Backward compatibility mappings
        palette: {
          midnight: "#0A0F1C",
          darkviolet: "#101827",
          violet: "#151E30",
          purple: "#6C63FF",
          royal: "#4EA1FF",
          blue: "#4EA1FF",
          periwinkle: "#4EA1FF",
          ice: "#F5F7FB",
        },
        obsidian: {
          950: "#0A0F1C",
          900: "#101827",
          850: "#151E30",
          800: "#1E2A42",
          700: "#26344D",
          600: "#384B6E",
          500: "#4EA1FF",
          400: "#75B6FF",
          300: "#9ECBFF",
          200: "#C7E1FF",
          100: "#E5F0FF",
          50: "#F5F7FB",
        },
        industrial: {
          950: "#0A0F1C",
          900: "#101827",
          850: "#151E30",
          800: "#1E2A42",
          700: "#26344D",
          600: "#384B6E",
          500: "#4EA1FF",
          400: "#75B6FF",
          300: "#9ECBFF",
          200: "#C7E1FF",
          100: "#E5F0FF",
          50: "#F5F7FB",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "-apple-system", "BlinkMacSystemFont", "'Segoe UI'", "Roboto", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.25s ease-in-out",
        "slide-up": "slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
        "pulse-subtle": "pulseSubtle 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSubtle: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
