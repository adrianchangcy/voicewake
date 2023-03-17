<template>
    <div class="py-1">
        <VPlayback
            ref="originator_audio"
        />
    </div>
    <VLikeDislike
        :propLikeCount="1099"
    />

    
</template>


<script setup lang="ts">

    // import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VLikeDislike from '/src/components/medium/VLikeDislike.vue';

</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    // const axios = require('axios');

    export default defineComponent({
        data() {
            return {
                passed_data: {'originator_event': null as any|null, 'responder_events': null as any|[]},
            };
        },
        beforeMount(){
        

        }
    });
</script>