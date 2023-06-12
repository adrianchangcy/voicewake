<template>
    <button
        :class="[
            (propIsEnabled ? 'text-theme-light hover:shadow-sm hover:shadow-theme-soft-danger/75 hover:bg-theme-danger hover:border-theme-light-trim/30' : 'text-theme-light/50 shadow-md cursor-default'),
            'h-10 text-2xl      rounded-lg border-t-2 shadow-md    bg-theme-danger/90 border-theme-light-trim/40 shadow-theme-soft-danger/75   transition'
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
        },
    });
</script>