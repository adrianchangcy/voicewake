<template>
    <div class="relative w-full h-full">
        <TransitionGroup
            name="transition-group-fade-slow"
            enter-from-class="opacity-0"
            :enter-active-class="propIsSwapping ? 'absolute transition-opacity delay-500 duration-500 ease-in-out' : 'transition-opacity delay-500 duration-500 ease-in-out'"
            enter-to-class="opacity-100"
            leave-from-class="opacity-100"
            :leave-active-class="propIsSwapping ? 'absolute transition-opacity duration-500 ease-in-out' : 'transition-opacity duration-500 ease-in-out'"
            leave-to-class="opacity-0"
        >
            <slot></slot>
        </TransitionGroup>
    </div>
</template>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        props: {
            propIsSwapping: {
                type: Boolean,
                default: false
            },
        },
    });
</script>