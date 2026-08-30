/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0F1420',
        surface: '#1A2130',
        textPrimary: '#F1F3F6',
        textMuted: '#94A0B8',
        positive: '#34D399',
        negative: '#F87171',
        neutral: '#94A3B8',
        amber: '#FBBF24',
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
