<template>
    <button
        :class="[
            (propIsEnabled ? 'text-theme-black hover:shadow-md hover:shadow-theme-lead/75 hover:bg-theme-soft-lead hover:border-theme-light-trim/40' : 'text-theme-black/10 shadow-md cursor-default'),
            (propIsSmaller ? 'w-20 h-20 text-lg font-medium' : 'w-32 h-32 sm:w-40 sm:h-40 text-2xl'),
            'block mx-auto      rounded-full border-t-2 shadow-lg    bg-theme-soft-lead/80 border-theme-light-trim shadow-theme-lead/75   transition duration-150 ease-in-out'
        ]"
        type="button"
    >
        <slot></slot>
    </button>
</template>


<script lang="ts">
    //focus:border-2 focus:outline-none focus:ring-1 focus:ring-theme-black focus:border-theme-black
    //for all buttons, change our hover css to click, and come up with another css for hover

    //we do not handle :disabled for buttons,
    //because it prevents other elements from dragging when mouse goes over :disabled elements
    //also decided not to use cursor-not-allowed, because it only registers if your mouse moves
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {

            };
        },
        props:{
            propIsEnabled: {
                type: Boolean,
                default: true
            },
            propIsSmaller: {
                type: Boolean,
                default: false
            },
        },
    });
</script>