<template>
    <!--specify a fixed height at parent, based on tallest possible child-->
    <div class="relative w-full h-full flex flex-col overflow-hidden">
        <TransitionGroup
            name="transition-group-slide"
            :enter-from-class="propIsForward ? 'opacity-0 translate-x-full' : 'opacity-0 -translate-x-full'"
            enter-active-class="transition delay-150"
            enter-to-class="opacity-100 transition-x-0"
            leave-from-class="opacity-100 transition-x-0"
            leave-active-class="transition absolute"
            :leave-to-class="propIsForward ? 'opacity-0 -translate-x-full' : 'opacity-0 translate-x-full'"
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
            propIsForward: {
                type: Boolean,
                default: true
            },
        },
    });
</script>