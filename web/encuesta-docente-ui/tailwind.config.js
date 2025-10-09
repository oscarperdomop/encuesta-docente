/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "usco-primary": "#8a1c1c", // rojo institucional aprox
      },
      boxShadow: {
        card: "0 8px 20px rgba(0,0,0,0.06)",
      },
      borderRadius: {
        "2xl": "1rem",
      },
    },
  },
  plugins: [],
};
