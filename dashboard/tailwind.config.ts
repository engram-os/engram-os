import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        // Warm terracotta — Engram's single accent. Everything else stays neutral.
        accent: {
          50:  '#FDF5F1',
          100: '#FAE7DE',
          200: '#F4CDBB',
          300: '#ECAB8E',
          400: '#E28A64',
          500: '#D97757',
          600: '#C05C3C',
          700: '#9E4A30',
          800: '#7E3C28',
          900: '#663224',
        },
      },
      keyframes: {
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
      animation: {
        'fade-up': 'fade-up 250ms ease-out both',
        'fade-in': 'fade-in 200ms ease-out both',
      },
    },
  },
  plugins: [],
} satisfies Config;
