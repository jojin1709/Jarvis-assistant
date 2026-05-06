export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void: "#02040a",
        panel: "rgba(5, 16, 28, 0.74)",
        cyanCore: "#38f6ff",
        cyanSoft: "#7defff",
        violetCore: "#a855f7",
      },
      fontFamily: {
        display: ["Orbitron", "Rajdhani", "Segoe UI", "sans-serif"],
        body: ["Rajdhani", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        neon: "0 0 24px rgba(56, 246, 255, 0.38)",
        panel: "0 0 32px rgba(20, 184, 255, 0.12)",
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        hudPulse: {
          "0%, 100%": { opacity: "0.35" },
          "50%": { opacity: "0.92" },
        },
      },
      animation: {
        scan: "scan 7s linear infinite",
        hudPulse: "hudPulse 2.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
