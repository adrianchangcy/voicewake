/** @type {import('tailwindcss').Config} */
module.exports = {
    //mode: 'jit', //so far not needed
    content: [
        "./voicewake/templates/**/*.html",
        "./voicewake/static/**/*.js",
        "./frontend/src/**/*.{vue,js,ts,jsx,tsx}",
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

/*
While docs say you can put this file in a subdirectory,
you actually can only put this in project root.
There are a few issue reports on this matter, but they are closed.
Also, the "../" trick to specify "exit to parent directory by one step" does not work.

mode:'jit', do i need it?
*/