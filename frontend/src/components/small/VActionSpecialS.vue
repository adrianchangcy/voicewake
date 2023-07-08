<template>
    <component
        :is="propElement"
        :class="[
            (propIsEnabled ? '' : 'opacity-30'),
            (propIsRound ? 'w-10 rounded-full' : 'rounded-lg'),
            'h-10 text-base font-medium flex items-center      border-t-2    bg-theme-soft-lead/80 border-theme-light-trim shadow-theme-lead/60   transition    text-theme-black shadow-md hover:shadow-sm hover:shadow-theme-lead/60 hover:bg-theme-soft-lead hover:border-theme-light-trim/40'
        ]"
        :disabled="!propIsEnabled"
    >
        <slot></slot>
    </component>
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
            propElement: {
                type: String,
                required: true
            },
            propIsRound: {
                type: Boolean,
                default: false
            },
        },
    });
</script>