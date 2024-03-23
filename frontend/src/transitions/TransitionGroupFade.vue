<template>
    <div class="relative w-full h-full">
        <TransitionGroup
            name="transition-group-fade"
            enter-from-class="opacity-0"
            :enter-active-class="propIsSwapping ? 'absolute transition-opacity delay-150' : 'transition-opacity delay-150'"
            enter-to-class="opacity-100"
            leave-from-class="opacity-100"
            :leave-active-class="propIsSwapping ? 'absolute transition-opacity' : 'transition-opacity'"
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