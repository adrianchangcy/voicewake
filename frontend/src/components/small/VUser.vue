<template>
    <button
    class="w-fit h-10 text-base font-extralight rounded-lg shade-when-hover transition-colors duration-200 ease-in-out"
    type="button"
    href='www.youtube.com'
>
    <span><i class="fas fa-user"></i> {{propUsername}}</span>
</button>
</template>


<script setup lang="ts">
</script>


<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        props: {
            propUsername: {
                type: String,
                default: ''
            },
        }
    });
</script>