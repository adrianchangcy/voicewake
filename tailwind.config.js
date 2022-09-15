/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./voicewake/templates/**/*.html",
    "./voicewake/static/**/*.js",
  ],
  theme: {
    extend: {
        colors: {
            'theme-light': '#F2F4F3',
            'theme-dark': '#22333B',

            'theme-cream': '#F8F9F0',
            'theme-red': '#A4243B',

            'theme-blue-1': '#1BC4FF',
            'theme-blue-2': '#00ABE7',


            'theme-yellow-light': '#FFE178',
            'theme-yellow-medium': '#FFD645',
            'theme-yellow-strong': '#EEBA0B',

            'theme-mud': '#82846D',

            'theme-cream-pink': '#F9F0F8',
        }
    },
  },
  plugins: [],
}
