<template>
    <CreateAudioClips
        :propIsOriginator="true"
        @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
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
    import { CreateAudioClips__isSubmitSuccessfulTypes } from '@/types/General.interface';

    export default defineComponent({
        data(){
            return {
            };
        },
        name: 'CreateEventsApp',
        methods: {
            async handleIsSubmitSuccessful(new_data:CreateAudioClips__isSubmitSuccessfulTypes) : Promise<void> {

                if(
                    new_data['is_successful'] === true &&
                    new_data['event_id'] !== null
                ){

                    //redirect
                    //no need to be concerned with form submit issue on back navigation, no issues
                    window.location.href = window.location.origin + "/event/" + new_data['event_id'].toString();
                }
            },
        },
    });
</script>


