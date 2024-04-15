/** @type {import('tailwindcss').Config} */
module.exports = {
    //use parent .dark to enable dark mode for child elements
    darkMode: ['class', '[class="dark"]'],
    //mode: 'jit', //so far not needed
    content: [
        "./voicewake/templates/**/*.html",
        "./voicewake/static/**/*.{js,svg}",
        "./frontend/src/**/*.{vue,js,ts,jsx,tsx}",
        //attempt to fix Tailwind requiring hard refresh for new class uses
        //https://stackoverflow.com/a/75099477
        "!./node_modules",
    ],
    // experimental: {
        //may help with slow Tailwind when item list is huge
        //https://github.com/tailwindlabs/tailwindcss/discussions/7411
        // optimizeUniversalDefaults: true
    // },
    theme: {
        extend: {
            //for transition duration
            //for chaining miscellaneous things, e.g. anime, is duration 100
            //hover, e.g. button, is duration-150
            //open/close, e.g. menu, is duration-200
            //long animation is duration-1000

            //remember to change the values in animeJS if you make changes here
            colors: {

                
                'theme-lead': '#facc15', //yellow-400

                //for small but high attention items, e.g. focus, highlight, etc.

                'theme-green-1': '#90a955',
                'theme-green-2': '#4f772d',
                'theme-green-3': '#31572c',

                'theme-danger': '#FA1414',
                'theme-soft-danger': '#F5DCDC',

                'theme-light': '#FEFAE6',
                'theme-light-trim': '#FDFDFD',
                'theme-black': '#404040',   //scaled via shades generator from theme-light
                //for disabled feature, advised to use opacity on entire element until unreadable, not gray background
                'theme-gray-1': '#e6e8da',
                'theme-gray-2': '#e1e3d5',
                'theme-gray-3': '#dee0d3',
                'theme-gray-4': '#94928b',
                'theme-gray-5': '#7a7973',
                'theme-outline': '#7a7973',

                'theme-dark': '#010a14',
                'theme-dark-trim': '#2a2b2e',
                'dark-theme-black': '#0d131a',
                'dark-theme-white': '#d9d9d9',
                'dark-theme-gray-1': '#212224',
                'dark-theme-gray-2': '#2f3033',
                'dark-theme-gray-3': '#3B3C40',
                'dark-theme-gray-4': '#4B4C52',
                'dark-theme-gray-5': '#61636B',
                'dark-theme-outline': '#61636B',

                'theme-cream': '#F8F9F0',
                'theme-red': '#A4243B',

                'theme-blue-1': '#1BC4FF',
                'theme-blue-2': '#00ABE7',

                'theme-mud': '#82846D',

                'theme-cream-pink': '#F9F0F8',
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
            },
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