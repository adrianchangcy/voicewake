<template>
    <!--parent div should look like:-->
    <!--<div class="relative">-->
    <TransitionGroup
        name="transition-group-fade-slow"
        enter-from-class="opacity-0"
        :enter-active-class="propHasAbsolute ? 'transition-opacity absolute delay-500 duration-500 ease-in-out' : 'transition-opacity'"
        enter-to-class="opacity-100"
        leave-from-class="opacity-100"
        :leave-active-class="propHasAbsolute ? 'transition-opacity absolute duration-500 ease-in-out' : 'transition-opacity'"
        leave-to-class="opacity-0"
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
            propHasAbsolute: {
                type: Boolean,
                default: false
            },
        },
    });
</script>