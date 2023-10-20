<template>
    <component
        :is="propElement"
        :class="[
            propFontSize === 's' ? 'text-base font-medium' : '',
            propFontSize === 'm' ? 'text-xl font-medium' : '',
            propElementSize === 's' ? 'h-10' : '',
            propIsEnabled ? '' : 'opacity-30',
            propIsDefaultOutlineOffset ? 'focus-visible:outline-offset-0' : 'focus-visible:-outline-offset-2',
            'block shade-text-when-hover rounded-lg transition   text-theme-black    focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-theme-outline'
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
            propIsDefaultOutlineOffset: {
                type: Boolean,
                default: true
            },
        }
    });
</script>