<template>
    <!--you'll need overflow-hidden relative for parent, and p-2 for child to counter parent's overflow-hidden-->
    <Transition
        name="transition-group-fade"
        :enter-from-class="propIsForward ? 'opacity-0 translate-x-full' : 'opacity-0 -translate-x-full'"
        enter-active-class="transition delay-150"
        enter-to-class="opacity-100 transition-x-0"
        leave-from-class="opacity-100 transition-x-0"
        leave-active-class="transition absolute"
        :leave-to-class="propIsForward ? 'opacity-0 -translate-x-full' : 'opacity-0 translate-x-full'"
    >
        <slot></slot>
    </Transition>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        props: {
            propIsForward: {
                type: Boolean,
                default: true
            },
        },
    });
</script>