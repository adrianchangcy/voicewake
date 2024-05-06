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
        "!./frontend/node_modules",
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

            //remember to change the values in helper_functions.drawCanvasRipples() if you make changes here
            colors: {
                'theme-light': '#FEFAE6',
                'theme-light-trim': '#FDFDFD',
                'theme-lead': '#facc15', //yellow-400
                'theme-black': '#404040',   //scaled via shades generator from theme-light
                //for disabled feature, advised to use opacity on entire element until unreadable, not gray background
                'theme-gray-1': '#e6e8da',
                'theme-gray-2': '#e1e3d5',
                'theme-gray-form-field': '#caccc0',    //for normal borders, hover to
                'theme-gray-3': '#c5c7bb',
                'theme-gray-4': '#807e78',
                'theme-gray-5': '#6b6a65',
                'theme-outline': '#6b6a65',

                'theme-dark': '#121212',
                'theme-dark-trim': '#2e2e2e',
                'dark-theme-lead': '#cca610',
                'dark-theme-black-1': '#1a1a1a',
                'dark-theme-black-2': '#1f1f1f',
                'dark-theme-white-1': '#e0dece',
                'dark-theme-white-2': '#adaba0',
                'dark-theme-gray-1': '#292929',
                'dark-theme-gray-2': '#3d3d3d',
                'dark-theme-gray-form-field': '#424242',
                'dark-theme-gray-3': '#474747',
                'dark-theme-gray-4': '#7a7a7a',
                'dark-theme-gray-5': '#999999',
                'dark-theme-outline': '#999999',

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
            boxShadow: {
                //Tailwind has two shadows, the second being for more shadow
                //the 4th value is based on Tailwind's second shadow's 3rd value, basically second shadow's thickness
                //smaller than Tailwind's, due to width space constraint at VUserLogInSignUp
                'surround-sm': '0 0 2px 0 rgb(0 0 0 / 0.05)',
                'surround-md': '0 0 4px 0 rgb(0 0 0 / 0.1)',
                'surround-lg': '0 0 8px 0 rgb(0 0 0 / 0.1)',
            },
            fontWeight: {
                //for default font, medium at 500 and 501 are ok for Chrome, but Firefox needs 501
                'medium': '501',
                'bold': '601',
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