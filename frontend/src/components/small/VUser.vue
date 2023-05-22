<template>
    <div class="w-fit overflow-hidden text-ellipsis whitespace-nowrap text-theme-black shade-text-when-hover transition-colors duration-200 ease-in-out">
        <a href="yolo">
            <i class="fas fa-user text-lg"></i> <span class="text-sm">{{ propUsername }}</span>
        </a>
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