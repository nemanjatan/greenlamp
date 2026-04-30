/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        script: ['"Caveat"', "cursive"],
      },
      colors: {
        // Brand-aligned with writetofreedom.com / scottscheper.com:
        // cream paper bg, dark navy ink, warm gold accent, hand-signed feel.
        paper: "#faf6ee",
        ink: {
          DEFAULT: "#1f2937",
          soft: "#475569",
          mute: "#94a3b8",
        },
        gold: {
          DEFAULT: "#b88a3e",
          soft: "#d4a557",
          deep: "#8a652a",
          tint: "#f5ecd9",
        },
        rule: "#e6dfce",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: 0, transform: "translateY(8px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out",
      },
      boxShadow: {
        page: "0 1px 0 rgba(31, 41, 55, 0.04), 0 8px 24px -12px rgba(31, 41, 55, 0.10)",
        card: "0 1px 0 rgba(31, 41, 55, 0.04), 0 16px 40px -20px rgba(31, 41, 55, 0.18)",
      },
    },
  },
  plugins: [],
};
