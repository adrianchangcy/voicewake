<template>
    <button
        :class="[
            (propIsDefaultColour ? 'bg-theme-light/60' : ''),
            (propIsDefaultTextSize ? 'text-2xl' : ''),
            (propIsEnabled ? 'hover:bg-theme-light/80 hover:border-theme-light-trim/40 hover:shadow-sm hover:scale-[0.99]' : 'opacity-10 cursor-default'),
            'h-10 p-1       border-t-2 border-theme-light-trim rounded-lg shadow-md transition duration-150 ease-in-out'
        ]"
    >
        <slot></slot>
    </button>
</template>


<script>
    //focus:border-2 focus:outline-none focus:ring-1 focus:ring-theme-black focus:border-theme-black
    //for all buttons, change our hover css to click, and come up with another css for hover

    //we do not handle :disabled for buttons,
    //because it prevents other elements from dragging when mouse goes over :disabled elements
    //also decided not to use cursor-not-allowed, because it only registers if your mouse moves

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
            propIsEnabled: {
                type: Boolean,
                default: true
            },
        },
    }
</script>