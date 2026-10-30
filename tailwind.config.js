/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hema: {
          bgDeep: '#04060c',
          bgNavy: '#0a1220',
          panel: 'rgba(10, 22, 38, 0.75)',
          panelSolid: '#0b1626',
          panelHover: '#10223b',
          border: 'rgba(0, 229, 255, 0.35)',
          borderGlow: 'rgba(0, 229, 255, 0.65)',
          cyan: '#00e5ff',
          blue: '#2f6bff',
          violet: '#7b5cff',
          text: '#d8f6ff',
          textDim: '#6f9bb3',
          ok: '#28e0a6',
          warn: '#ffc457',
          danger: '#ff4d6d',
        }
      },
      fontFamily: {
        sans: ['"Segoe UI"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"Cascadia Mono"', 'Consolas', '"DejaVu Sans Mono"', 'monospace'],
      },
      boxShadow: {
        'cyan-glow': '0 0 20px rgba(0, 229, 255, 0.25)',
        'cyan-glow-lg': '0 0 35px rgba(0, 229, 255, 0.4)',
        'blue-glow': '0 0 20px rgba(47, 107, 255, 0.3)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 12s linear infinite',
        'spin-reverse': 'spin-reverse 16s linear infinite',
      },
      keyframes: {
        'spin-reverse': {
          '0%': { transform: 'rotate(360deg)' },
          '100%': { transform: 'rotate(0deg)' },
        }
      }
    },
  },
  plugins: [],
}
