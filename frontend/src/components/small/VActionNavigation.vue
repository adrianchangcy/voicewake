<template>
    <component
        :is="propElement"
        :class="[
            propIsEnabled ? 'text-theme-black' : 'text-theme-black/10',
            propUseDefaultHeight ? 'h-10' : '',
            'flex items-center text-xl font-medium shade-text-when-hover rounded-lg transition-colors'
        ]"
        :disabled="!propIsEnabled"
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
            propIsEnabled: {
                type: Boolean,
                default: true
            },
            propUseDefaultHeight: {
                type: Boolean,
                default: true
            },
        }
    });
</script>