/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        bg: '#0b1220',
        'bg-soft': '#0f172a',
        card: '#121a2c',
        text: '#e5e7eb',
        muted: '#9ca3af',
        brand: '#0ea5e9',
        'brand-weak': '#38bdf8',
        danger: '#ef4444',
        ok: '#22c55e',
        warning: '#f59e0b'
      }
    },
  },
  plugins: [],
}