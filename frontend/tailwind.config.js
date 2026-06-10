/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        nova: {
          green:  '#22c55e',
          red:    '#ef4444',
          amber:  '#f59e0b',
          blue:   '#3b82f6',
          purple: '#8b5cf6',
          dark:   '#0f172a',
          panel:  '#1e293b',
          card:   '#263347',
          border: '#334155',
          text:   '#e2e8f0',
          muted:  '#94a3b8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    }
  },
  plugins: []
}
