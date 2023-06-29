<template>
    <component
        :is="propElement"
        :class="[
            propUseDefaultHeight ? 'h-10' : '',
            'flex items-center text-xl font-medium text-theme-black shade-text-when-hover rounded-lg transition-colors'
        ]"
    >
        <slot></slot>
    </component>
</template>

<script>
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {

            };
        },
        props: {
            propElement: {
                type: String,
                required: true
            },
            propUseDefaultHeight: {
                type: Boolean,
                default: true
            },
        }
    });
</script>