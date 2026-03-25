/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gjp: '#0b948f', // 客户的专属青色
      }
    },
  },
  plugins: [],
}