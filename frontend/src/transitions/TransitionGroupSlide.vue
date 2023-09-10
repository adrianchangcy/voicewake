<template>
    <!--parent div should look like:-->
    <!--<div class="h-[your_height+all_padding] overflow-hidden relative">-->
    <TransitionGroup
        name="transition-group-fade"
        :enter-from-class="propIsForward ? 'opacity-0 translate-x-full' : 'opacity-0 -translate-x-full'"
        enter-active-class="transition delay-150"
        enter-to-class="opacity-100 transition-x-0"
        leave-from-class="opacity-100 transition-x-0"
        leave-active-class="transition absolute"
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