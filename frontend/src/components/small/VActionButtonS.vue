<template>
    <button
        :class="[
            (propIsEnabled ? 'hover:bg-theme-light/80 hover:border-theme-light-trim/40 hover:shadow-sm' : 'opacity-10 cursor-default'),
            'h-10 text-base font-medium flex items-center bg-theme-light/60       border-t-2 border-theme-light-trim rounded-lg shadow-md transition'
        ]"
        type="button"
        :disabled="!propIsEnabled"
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
        },
    });
</script>