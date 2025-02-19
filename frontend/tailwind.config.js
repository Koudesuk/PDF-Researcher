/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      backdropFilter: {
        'none': 'none',
        'blur': 'blur(2px)',
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            p: {
              marginTop: '0.5em',
              marginBottom: '0.5em',
            },
            'h1, h2, h3, h4, h5, h6': {
              marginTop: '0.5em',
              marginBottom: '0.5em',
            },
          },
        },
        compact: {
          css: {
            p: {
              marginTop: '0.25em',
              marginBottom: '0.25em',
            },
            'h1, h2, h3, h4, h5, h6': {
              marginTop: '0.25em',
              marginBottom: '0.25em',
            },
          },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}