<template>
    <component
        :is="propElement"
        :class="[
            propFontSize === 's' ? 'text-base font-medium' : '',
            propFontSize === 'm' ? 'text-xl font-medium' : '',
            propElementSize === 's' ? 'h-10' : '',
            propIsEnabled ? '' : 'opacity-30',
            'flex items-center shade-text-when-hover rounded-lg transition-colors   text-theme-black'
        ]"
        :disabled="!propIsEnabled"
    >
        <slot></slot>
    </component>
</template>

<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import ElementSizes from '@/types/values/ElementSizes';

    export default defineComponent({
        data(){
            return {

            };
        },
        props: {
            propFontSize: {
                type: String as PropType<ElementSizes>,
                default: "",
            },
            propElementSize: {
                type: String as PropType<ElementSizes>,
                default: "",
            },
            propElement: {
                type: String,
                required: true
            },
            propIsEnabled: {
                type: Boolean,
                default: true
            },
        }
    });
</script>