/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bayora: {
          sidebar: "#F4F3FA", // Tasteful pale lavender sidebar
          sidebarActive: "#EBE8F7",
          sidebarBorder: "#E2DFEE",
          primary: "#2563EB",
          primaryHover: "#1D4ED8",
          cyan: "#06B6D4",
          blue: "#3B82F6",
          dark: "#0F172A",
          muted: "#64748B",
          cardBg: "#FFFFFF",
          workspace: "#F8FAFC"
        },
        severity: {
          critical: "#EF4444",
          criticalBg: "#FEF2F2",
          criticalBorder: "#FCA5A5",
          high: "#F97316",
          highBg: "#FFF7ED",
          highBorder: "#FDBA74",
          medium: "#F59E0B",
          mediumBg: "#FEFCE8",
          mediumBorder: "#FDE047",
          low: "#3B82F6",
          lowBg: "#EFF6FF",
          lowBorder: "#93C5FD",
          clean: "#10B981",
          cleanBg: "#ECFDF5",
          cleanBorder: "#A7F3D0"
        }
      },
      fontFamily: {
        heading: ["'Space Grotesk'", "sans-serif"],
        body: ["'Manrope'", "'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"]
      }
    },
  },
  plugins: [],
}
