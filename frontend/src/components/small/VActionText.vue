<template>
    <component
        :is="propElement"
        :class="[
            propFontSize === 's' ? 'text-base font-medium' : '',
            propFontSize === 'm' ? 'text-xl font-medium' : '',
            propElementSize === 's' ? 'h-10' : '',
            propIsEnabled ? '' : 'opacity-30',
            'block transition-colors rounded-lg    action-text-hover active:bg-theme-gray-3 dark:active:bg-dark-theme-gray-3 origin-center transform     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline'
        ]"
        :disabled="!propIsEnabled"
    >
        <!--current font sinks too low, hence pb-->
        <div class="w-full h-full flex items-center pretty-font">
            <slot></slot>
        </div>
    </component>
</template>

<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import LetterSizeValues from '@/types/values/LetterSizeValues';

    export default defineComponent({
        data(){
            return {

            };
        },
        props: {
            propFontSize: {
                type: String as PropType<LetterSizeValues>,
                default: "",
            },
            propElementSize: {
                type: String as PropType<LetterSizeValues>,
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