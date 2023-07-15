<template>
    <component
        :is="propElement"
        :class="[
            propFontSize === '2xl' ? 'text-2xl font-medium' : '',
            propFontSize === 'xl' ? 'text-2xl font-medium' : '',
            propFontSize === 'l' ? 'text-2xl font-medium' : '',
            propFontSize === 'm' ? 'text-2xl font-medium' : '',
            propFontSize === 's' ? 'text-base font-medium' : '',
            propElementSize === '2xl' ? 'h-40 shadow-lg hover:shadow-md' : '',
            propElementSize === 'xl' ? 'h-32 shadow-lg hover:shadow-md' : '',
            propElementSize === 'l' ? 'h-24 shadow-lg hover:shadow-md' : '',
            propElementSize === 'm' ? 'h-20 shadow-lg hover:shadow-md' : '',
            propElementSize === 's' ? 'h-10 shadow-md hover:shadow-sm' : '',
            propIsEnabled ? '' : 'opacity-30',
            propIsRound ? 'rounded-full' : 'rounded-lg',
            'block transition       text-theme-black border-t-2    bg-theme-light/60 hover:bg-theme-light/80      border-theme-light-trim hover:border-theme-light-trim/40'
        ]"
        :disabled="!propIsEnabled"
    >
        <!--current font sinks too low, hence pb-->
        <div class="w-full h-full pb-0.5 grid items-center">
            <slot></slot>
        </div>
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
            propIsRound: {
                type: Boolean,
                default: false
            },
            propIsEnabled: {
                type: Boolean,
                default: true
            },
        }
    });
</script>