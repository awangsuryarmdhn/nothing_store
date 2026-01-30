// @ts-check
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './nothing_brain_project/**/*.py', 
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Archivo Black', 'sans-serif'],
      },
      colors: {
        brand: {
          black: '#0a0a0a',
          dark: '#1a1a1a',
          gray: '#2a2a2a',
          accent: '#ffffff',
        }
      }
    },
  },
  plugins: [],
  daisyui: {
    themes: ['lofi'],
  }
}
