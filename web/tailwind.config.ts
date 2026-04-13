import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,js}"],
  theme: {
    extend: {
      colors: {
        coral: {
          50: "#fef2f0",
          100: "#fde3df",
          200: "#fcc8bf",
          300: "#f9a494",
          400: "#ed7b67",
          500: "#e05a45",
          600: "#c4402d",
          700: "#a33222",
          800: "#872c20",
          900: "#712921",
          950: "#3d120d",
        },
        gold: {
          50: "#fdf8eb",
          100: "#f9ecc8",
          200: "#f3d88d",
          300: "#edc052",
          400: "#d89e43",
          500: "#d08b24",
          600: "#b86b1b",
          700: "#934d19",
          800: "#7a3e1b",
          900: "#68341c",
          950: "#3c1a0c",
        },
        merino: {
          50: "#faf7f2",
          100: "#f7f2e8",
          200: "#ede3d0",
          300: "#e0ceb1",
          400: "#d1b38e",
          500: "#c49c74",
          600: "#b78662",
          700: "#997052",
          800: "#7c5c47",
          900: "#664d3c",
          950: "#342016",
        },
        bark: {
          DEFAULT: "#5a4627",
          light: "#7a6440",
          dark: "#342016",
        },
      },
      fontFamily: {
        display: ['"Nunito"', "sans-serif"],
        body: ['"Nunito"', "sans-serif"],
      },
      borderRadius: {
        card: "1.25rem",
      },
    },
  },
  plugins: [],
} satisfies Config;
