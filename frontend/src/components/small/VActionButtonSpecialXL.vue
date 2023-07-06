<template>
    <button
        :class="[
            (propIsEnabled ? '' : 'opacity-30'),
            (propIsSmaller ? 'scale-50' : ''),
            'w-40 h-40 text-2xl flex items-center      rounded-full border-t-2     bg-theme-soft-lead/80 border-theme-light-trim shadow-theme-lead/75   text-theme-black shadow-lg hover:shadow-md hover:shadow-theme-lead/75 hover:bg-theme-soft-lead hover:border-theme-light-trim/40   transition'
        ]"
        type="button"
        :disabled="!propIsEnabled"
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