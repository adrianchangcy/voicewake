<template>
    <div>
        <a href="www.youtube.com">
            <span class="text-theme-black text-base rounded-lg hover:underline transition-colors duration-200 ease-in-out">
                <i class="fas fa-user text-xl"></i> {{ propUsername }}
            </span>
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
        }
    });
</script>