<template>
    <CreateAudioClips
        :propIsOriginator="true"
        @isSubmitSuccessful="handleIsSubmitSuccessful($event)"
    />
</template>

<script setup lang="ts">
    import CreateAudioClips from '/src/components/main/CreateAudioClips.vue';
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
        }
    });
</script>


