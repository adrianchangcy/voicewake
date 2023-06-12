<template>
    <button
        class="w-fit h-10 rounded-lg text-theme-black text-lg font-medium transition-colors underline underline-offset-2 decoration-2"
        :class="propIsEnabled ? 'handle-action-text-when-hover decoration-theme-black' : 'decoration-theme-black/0'"
        :disabled="!propIsEnabled"
        type="button"
    >
        <slot></slot>
    </button>
</template>


<script lang="ts">
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