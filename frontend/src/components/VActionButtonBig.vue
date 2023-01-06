<template>
    <button
        :class="[
            (propIsDefaultColour ? 'bg-theme-light/60 hover:bg-theme-light/80' : ''),
            (propIsDefaultTextSize ? 'text-2xl' : ''),
            (propIsDisabled ? 'cursor-not-allowed' : 'hover:border-theme-light-trim/40 hover:shadow-sm hover:scale-[0.99]'),
            'h-32       items-center border-t-2 border-theme-light-trim rounded-lg shadow-md transition duration-150 ease-in-out'
        ]"
        :disabled="propIsDisabled"
    >
        <slot></slot>
    </button>
</template>


<script>
    //focus:border-2 focus:outline-none focus:ring-1 focus:ring-theme-black focus:border-theme-black
    //for all buttons, change our hover css to click, and come up with another css for hover
    export default {
        data(){
            return {

            };
        },
        props:{
            propIsDefaultColour: {
                type: Boolean,
                default: true
            },
            propIsDefaultTextSize: {
                type: Boolean,
                default: true
            },
            propIsDisabled: {
                type: Boolean,
                default: false
            },
        },
    }
</script>