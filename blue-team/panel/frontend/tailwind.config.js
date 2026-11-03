/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        soc: { bg: '#0b1120', panel: '#111a2e', border: '#1e2a44', muted: '#7c8db5', accent: '#38bdf8' },
        sev: { info: '#64748b', low: '#22c55e', medium: '#eab308', high: '#f97316', critical: '#ef4444' },
      },
      fontFamily: { mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'] },
    },
  },
  plugins: [],
}
