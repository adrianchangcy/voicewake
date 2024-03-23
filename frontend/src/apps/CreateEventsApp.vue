<template>
    <div class="relative border border-theme-gray-2 rounded-lg px-2 sm:px-4 pt-8 pb-12">
        <CreateAudioClips
            :propIsOriginator="true"
        />
    </div>

    <Teleport to="#create-events-header-logo">
        <FontAwesomeIcon icon="fas fa-comment"/>
    </Teleport>
</template>

<script setup lang="ts">
    import CreateAudioClips from '../components/main/CreateAudioClips.vue';

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


