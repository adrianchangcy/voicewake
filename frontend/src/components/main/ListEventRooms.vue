<template>
    <div>

        <VSectionTitle
            propTitle="Reply"
        />

        <VEventPending/>

        <div class="py-12">
            <VActionButtonBig class="w-full">
                More
            </VActionButtonBig>
        </div>


        <div class="sticky w-full h-fit bottom-0 z-40">
            <VPlayback
                :propIsSticky="true"
            />
        </div>
    </div>
</template>


<script setup lang="ts">
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VEventPending from '/src/components/medium/VEventPending.vue';
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VActionButtonBig from '../small/VActionButtonBig.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    // import EventTypes from '@/types/Events.interface';
    import { sortEvents } from '@/helper_functions';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                sorted_events: {} as any,
            };
        },
        mounted(){

            this.getEvents();
        },
        methods: {
            async getEvents(){

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/status/completed')
                .then((results:any) => {

                    //sort events
                    this.sorted_events = sortEvents(results.data);
                })
                .catch((errors:any) => {

                    console.log(errors);
                });
            },
        }
    });
</script>