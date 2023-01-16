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
            //for transition duration
            //for chaining miscellaneous things, e.g. anime, is duration 100
            //hover, e.g. button, is duration-150
            //open/close, e.g. menu, is duration-200
            //long animation is duration-1000

            //remember to change the values in animeJS if you make changes here
            colors: {

                
                // 'theme-lead': '#FFD645',    //this yellow isn't as nice as yellow-300
                'theme-lead': '#facc15', //yellow-400, for main colour

                'theme-light': '#F2F4F3',
                'theme-light-trim': '#FDFDFD',
                'theme-dark': '#22333B',

                'theme-ok': '#00ff00',
                'theme-warning': '#FFE178',
                'theme-danger': '#ff0000',

                //for disabled feature, advised to use opacity until unreadable, and not gray
                'theme-light-gray': '#e7e5e4',
                'theme-medium-gray': '#d6d3d1',
                'theme-dark-gray': '#a8a29e',

                'theme-black': '#444444',

                'theme-cream': '#F8F9F0',
                'theme-red': '#A4243B',

                'theme-blue-1': '#1BC4FF',
                'theme-blue-2': '#00ABE7',

                'theme-mud': '#82846D',

                'theme-cream-pink': '#F9F0F8',

                'theme-yellow': '#facc15', //yellow-400, not used as lead because it's too glaring
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