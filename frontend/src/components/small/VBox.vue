<template>
    <div
        :class="[
            propIsOpaque ? 'bg-theme-light/60 backdrop-blur' : 'bg-theme-light backdrop-blur-none',
            'border border-theme-dark-gray rounded-lg'
        ]"
    >
        <slot></slot>
    </div>
</template>


<script>
    import { defineComponent } from 'vue';

    export default defineComponent({
        props: {
            propIsOpaque: {
                type: Boolean,
                default: true
            }
        }
    });
</script>
