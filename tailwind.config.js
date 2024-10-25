/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/*.html',
    './**/templates/**/*.html',
    './store/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
   container: {
    center: true
   },
    extend: {
     fontFamily: {
      poppins: ['Poppins', 'sans-serif'],
      roboto: ['Roboto', 'sans-serif'],
      },
     colors: {
     'primary': '#1c1917',
     'base-primary': '#f5f5f4',
     'base-secondary': '#e2e2e2',
   },
    },
  },
  plugins: [
   ],
}



