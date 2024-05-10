<template>
    <component
        :is="propElement"
        :class="[
            propFontSize === '2xl' ? 'text-2xl font-medium' : '',
            propFontSize === 'xl' ? 'text-2xl font-medium' : '',
            propFontSize === 'l' ? 'text-2xl font-medium' : '',
            propFontSize === 'm' ? 'text-xl font-medium' : '',
            propFontSize === 's' ? 'text-base font-medium' : '',
            propElementSize === '2xl' ? 'h-40 shadow-lg dark:shadow-surround-lg active:shadow-md dark:active:shadow-surround-md' : '',
            propElementSize === 'xl' ? 'h-32 shadow-lg dark:shadow-surround-lg active:shadow-md dark:active:shadow-surround-md' : '',
            propElementSize === 'l' ? 'h-24 shadow-lg dark:shadow-surround-lg active:shadow-md dark:active:shadow-surround-md' : '',
            propElementSize === 'm' ? 'h-20 shadow-lg dark:shadow-surround-lg active:shadow-md dark:active:shadow-surround-md' : '',
            propElementSize === 's' ? 'h-10 shadow-md dark:shadow-surround-md active:shadow-sm dark:active:shadow-surround-sm' : '',
            propIsEnabled ? '' : 'opacity-30',
            propIsRound ? 'rounded-full' : 'rounded-lg',
            'block text-theme-light action-danger-hover border-t-2       bg-red-600 border-red-400 dark:border-transparent       active:bg-[#ad1a1a] active:border-red-600    shadow-red-500 dark:shadow-red-500      transition      focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-theme-outline dark:focus-visible:outline-dark-theme-outline'
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
                propElementSize === 's' ? 'pb-[0.1875rem]' : '',
                propElementSize === 'm' ? 'pb-[0.3125rem]' : '',
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
            propIsRound: {
                type: Boolean,
                default: false
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