<template>
    <div class="py-1">
        <VPlayback
            ref="originator_audio"
        />
    </div>
    <VLikeDislike
        :propEventId="10"
        :propLikeCount="800"
        :propDislikeCount="0"
        :propIsLiked="true"
    />

    
</template>


<script setup lang="ts">

    // import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VLikeDislike from '/src/components/medium/VLikeDislike.vue';

</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeDifferenceUTC } from '@/helper_functions';
    // const axios = require('axios');

    export default defineComponent({
        data() {
            return {
                passed_data: {'originator_event': null as any|null, 'responder_events': null as any|[]},
            };
        },
        beforeMount(){
        
            //change '1 Jan 2023' to '1 century ago'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            const container = document.getElementsByClassName('event-room')[0];
            const when_created_element = container.getElementsByClassName('when-created')[0];
            const when_created = (container.getAttribute('data-when-created') as string).replace(/ /g, 'T') + 'Z';
            when_created_element.textContent = timeDifferenceUTC(new Date(when_created));
        }
    });
</script>