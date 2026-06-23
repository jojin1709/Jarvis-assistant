export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "#070B14",
        panel: "rgba(15,23,42,0.72)",
        cyanCore: "#00E5FF",
        cyanSoft: "#8BEFFF",
        textPrimary: "#E6EDF3",
        textSecondary: "#94A3B8",
        line: "rgba(255,255,255,0.06)",
      },
      fontFamily: {
        display: ["Geist", "Inter", "Segoe UI", "sans-serif"],
        body: ["Inter", "Geist", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        premium: "0 24px 80px rgba(0, 0, 0, 0.38)",
        soft: "0 16px 48px rgba(0, 0, 0, 0.22)",
        accent: "0 18px 60px rgba(0, 229, 255, 0.12)",
      },
      keyframes: {
        softPulse: {
          "0%, 100%": { opacity: "0.55", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.04)" },
        },
      },
      animation: {
        softPulse: "softPulse 3.2s ease-in-out infinite",
      },
    },
  },
  plugins: [
    function ({ addVariant }) {
      addVariant("theme-light", '[data-theme="light"] &');
      addVariant("theme-midnight", '[data-theme="midnight"] &');
      addVariant("theme-graphite", '[data-theme="graphite"] &');
    },
  ],
};
