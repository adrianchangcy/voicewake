<template>
    <div class="pretty-font">
        <h1
            :class="[
                propFontSize === 'xl' ? 'text-5xl' : '',
                propFontSize === 'l' ? 'text-4xl' : '',
                propFontSize === 'm' ? 'text-xl font-medium' : '',
                propFontSize === 's' ? 'text-lg' : '',
                'h-fit break-words'
            ]"
        >
                <slot name="title"></slot>
        </h1>

        <h2
            :class="[
                propFontSize === 'xl' ? 'text-4xl' : '',
                propFontSize === 'l' ? 'text-xl font-medium' : '',
                propFontSize === 'm' ? 'text-lg' : '',
                propFontSize === 's' ? 'text-sm' : '',
                'h-fit break-words'
            ]"
        >
            <slot name="titleDescription"></slot>
        </h2>
    </div>
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
        },
    });
</script>