<template>
    <CreateAudioClips
        :propIsOriginator="true"
    />

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


