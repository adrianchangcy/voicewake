<template>
    <component
        :is="propElement"
        :class="[
            propFontSize === '2xl' ? 'text-2xl font-medium' : '',
            propFontSize === 'xl' ? 'text-2xl font-medium' : '',
            propFontSize === 'l' ? 'text-2xl font-medium' : '',
            propFontSize === 'm' ? 'text-xl font-medium' : '',
            propFontSize === 's' ? 'text-base font-medium' : '',
            propElementSize === '2xl' ? 'h-40' : '',
            propElementSize === 'xl' ? 'h-32' : '',
            propElementSize === 'l' ? 'h-24' : '',
            propElementSize === 'm' ? 'h-20' : '',
            propElementSize === 's' ? 'h-10' : '',
            propIsEnabled ? '' : 'opacity-30',
            'block     shade-border-when-hover active:bg-theme-lightest-gray transition-colors      bg-theme-light       border border-theme-light-gray rounded-full     focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-4 focus-visible:outline-theme-outline'
        ]"
        :disabled="!propIsEnabled"
    >
        <!--current font sinks too low, hence pb-->
        <div
            v-if="propIsIconOnly"
            class="w-full h-full flex items-center"
        >
            <slot></slot>
        </div>
        <div
            v-else
            :class="[
                propElementSize === 's' ? 'pb-0.5' : '',
                propElementSize === 'm' ? 'pb-1' : '',
                propElementSize === 'l' ? 'pb-2' : '',
                propElementSize === 'xl' ? 'pb-2' : '',
                propElementSize === '2xl' ? 'pb-2' : '',
                'w-full h-full flex items-center'
            ]"
        >
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
            propIsIconOnly: {   //if only fa icon, being absolute lets it not move lower like text would
                type: Boolean,
                default: false
            },
        }
    });
</script>