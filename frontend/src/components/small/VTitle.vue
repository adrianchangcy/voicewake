<template>
    <div class="text-theme-black">
        <div
            :class="[
                propFontSize === 'xl' ? 'text-5xl' : '',
                propFontSize === 'l' ? 'text-4xl' : '',
                propFontSize === 'm' ? 'text-xl font-medium' : '',
                propFontSize === 's' ? 'text-lg' : '',
                'h-fit break-words'
            ]"
        >
            <slot name="title"></slot>
        </div>
        <div
            :class="[
                propFontSize === 'xl' ? 'text-4xl' : '',
                propFontSize === 'l' ? 'text-xl font-medium' : '',
                propFontSize === 'm' ? 'text-base' : '',
                propFontSize === 's' ? 'text-base' : '',
                'h-fit break-words'
            ]"
        >
            <slot name="titleDescription"></slot>
        </div>
    </div>
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
        }
    });
</script>