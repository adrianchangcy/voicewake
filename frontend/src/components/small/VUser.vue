<template>
    <div class="w-full h-fit overflow-hidden flex flex-row gap-2 items-center text-theme-black text-sm">
        <i class="block h-fit fas fa-user"></i>
        <span class="block h-fit text-ellipsis whitespace-nowrap">{{ propUsername }}</span>
    </div>
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
        },
    });
</script>