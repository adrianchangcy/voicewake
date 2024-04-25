<template>
    <!--this is needed because font-awesome does not stay truly center-->
    <div class="w-fit h-fit flex flex-row items-center">
        <div
            :class="[
                propElementSize === '2xl' ? 'w-6 h-6 border-2' : '',
                propElementSize === 'xl' ? 'w-6 h-6 border-2' : '',
                propElementSize === 'l' ? 'w-6 h-6 border-2' : '',
                propElementSize === 'm' ? 'w-5 h-5 border-2' : '',
                propElementSize === 's' ? 'w-4 h-4 border-2' : '',
                propColourClass === '' ? 'border-theme-black dark:border-dark-theme-white-2' : propColourClass,
                'rounded-full border-l-transparent dark:border-l-transparent animate-spin'
            ]"
        ></div>
        <slot></slot>
    </div>
</template>


<script lang="ts">
    //we don't keep VAudioClipToneMenu in this component due to the inflexibility of button size =/= menu size
    import { defineComponent, PropType } from 'vue';
    import LetterSizeValues from '@/types/values/LetterSizeValues';

    export default defineComponent({
        data(){
            return{
            };
        },
        props: {
            propElementSize: {
                type: String as PropType<LetterSizeValues>,
                required: true
            },
            propColourClass: {
                type: String,
                default: ''
            },
        },
    });
</script>