/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        'bg-elev': 'var(--bg-elev)',
        text: 'var(--text)',
        muted: 'var(--muted)',
        primary: 'var(--primary)',
        ring: 'var(--ring)',
        card: 'var(--card)',
        border: 'var(--border)',
      },
      boxShadow: {
        card: '0 6px 24px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
};
