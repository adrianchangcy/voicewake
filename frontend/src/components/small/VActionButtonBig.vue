<template>
    <button
        :class="[
            (propIsEnabled ? 'hover:bg-theme-light/80 hover:border-theme-light-trim/40 shadow-theme-lead/75 shadow-lg hover:shadow-theme-lead/75 hover:shadow-md text-theme-black' : 'shadow-md hover:shadow-sm cursor-not-allowed text-theme-black/10'),
            'w-28 h-28 p-4 block text-2xl bg-theme-light/60       border-t-2 border-theme-light-trim rounded-full transition duration-150 ease-in-out'
        ]"
        type="button"
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
            propIsEnabled: {
                type: Boolean,
                default: true
            },
        },
    }
</script>