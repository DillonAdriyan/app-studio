/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './store/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
   container: {
    center: true
   },
   colors: {
    'primary': '#1c1917',
    'base-primary': '#f5f5f4',
   },
    extend: {
    },
  },
  plugins: [],
}



