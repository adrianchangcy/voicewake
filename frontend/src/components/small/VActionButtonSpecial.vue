<template>
    <button
        :class="[
            (propIsEnabled ? 'text-theme-black' : 'shadow-md hover:shadow-sm cursor-not-allowed text-theme-black/10'),
            (propIsProcessing ? 'cursor-wait' : ''),
            'w-40 h-40 mx-auto text-2xl bg-theme-soft-lead/80       border-t-2 border-theme-light-trim rounded-full   hover:bg-theme-soft-lead hover:border-theme-light-trim/40 shadow-theme-lead/75 shadow-lg hover:shadow-theme-lead/75 hover:shadow-md   transition duration-150 ease-in-out'
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
            propIsProcessing: {
                type: Boolean,
                default: false
            },
        },
    });
</script>