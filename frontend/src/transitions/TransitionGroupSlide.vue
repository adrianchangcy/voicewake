<template>
    <TransitionGroup
        name="transition-group-fade"
        :enter-from-class="propIsForward ? 'opacity-0 translate-x-full' : 'opacity-0 -translate-x-full'"
        enter-active-class="transition duration-200 ease-in-out delay-200"
        enter-to-class="opacity-100 transition-x-0"
        leave-from-class="opacity-100 transition-x-0"
        leave-active-class="transition duration-200 ease-in-out absolute"
        :leave-to-class="propIsForward ? 'opacity-0 -translate-x-full' : 'opacity-0 translate-x-full'"
    >
        <slot></slot>
    </TransitionGroup>
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