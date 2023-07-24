/** @type {import('tailwindcss').Config} */
module.exports = {
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

                
                // 'theme-lead': '#FFD645',    //this yellow isn't as nice as yellow-300
                'theme-lead': '#facc15', //yellow-400, for highlight
                'theme-soft-lead': '#f5f5dc',   //for background yellow

                //for small but high attention items, e.g. focus, highlight, etc.
                'theme-accent': '#a8a29e',

                'theme-green-1': '#90a955',
                'theme-green-2': '#4f772d',
                'theme-green-3': '#31572c',

                'theme-danger': '#fa3515',
                'theme-soft-danger': '#ff4934',

                'theme-light': '#F2F4F3',
                'theme-light-trim': '#FDFDFD',
                'theme-dark': '#22333B',

                'theme-toast-success': '#379d00',   //as text, or bg and use text-theme-light
                'theme-toast-warning': '#ffc500',   //as text, or bg and use text-theme-black
                'theme-toast-warning-2': '#daa520', //as text only
                'theme-toast-danger': '#d81a1a',    //as text, or bg and use text-theme-light
                'theme-toast': '#e6e6e6',           //as text, or bg and use text-theme-black

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