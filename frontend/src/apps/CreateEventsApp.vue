<template>
    <CreateAudioClips
        :propIsOriginator="true"
    />
</template>

<script setup lang="ts">
    import CreateAudioClips from '/src/components/main/CreateAudioClips.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'CreateEventsApp',
        methods: {
        }
    });
</script>


