<template>
    <div class="relative rounded-lg px-2 sm:px-4 pt-8 pb-12">
        <VCreateAudioClips
            :propIsOriginator="true"
        />
    </div>

    <Teleport to="#create-events-header-logo">
        <FontAwesomeIcon icon="fas fa-comment"/>
    </Teleport>
</template>

<script setup lang="ts">
    import VCreateAudioClips from '@/components/main/VCreateAudioClips.vue';

    import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    import { library } from '@fortawesome/fontawesome-svg-core';
    import { faComment } from '@fortawesome/free-solid-svg-icons/faComment';

    library.add(faComment);
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
        },
    });
</script>


