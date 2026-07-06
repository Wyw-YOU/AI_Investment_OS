/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        up: "#ef4444",
        down: "#22c55e",
      },
    },
  },
  plugins: [],
};
