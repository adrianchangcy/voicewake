<template>
    <component
        :is="propElement"
        :class="[
            propFontSize === 's' ? 'text-base font-medium' : '',
            propFontSize === 'm' ? 'text-xl font-medium' : '',
            propElementSize === 's' ? 'h-10' : '',
            propIsEnabled ? '' : 'opacity-30',
            'block shade-text-when-hover rounded-lg transition-colors   text-theme-black'
        ]"
        :disabled="!propIsEnabled"
    >
        <!--current font sinks too low, hence pb-->
        <div
            v-if="propIsIconOnly"
            class="w-full h-full grid items-center"
        >
            <slot></slot>
        </div>
        <div
            v-else
            :class="[
                propElementSize === 's' ? 'pb-0.5' : 'pb-1',
                'w-full h-full grid items-center'
            ]"
        >
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