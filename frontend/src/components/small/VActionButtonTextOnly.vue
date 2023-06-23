<template>
    <button
        :class="[
            propIsEnabled ? 'text-theme-black shade-text-when-hover' : 'text-theme-black/10',
            propUseDefaultHeight ? 'h-10' : '',
            'w-fit text-base font-medium flex items-center rounded-lg transition-colors'
        ]"
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
            propUseDefaultHeight: {
                type: Boolean,
                default: true
            },
        },
    });
</script>