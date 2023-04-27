<template>
    <div>
        <VSectionTitle
            propTitle="Reply"
        />

        <div class="flex flex-col gap-y-32">
            <div v-for="event_room in event_rooms" :key="event_room">
                <EventRoomCard
                    :propEventRoom="event_room"
                    :propIsMany="true"
                />
            </div>
        </div>

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
    import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VActionButtonBig from '/src/components/small/VActionButtonBig.vue';
    import EventRoomCard from '/src/components/main/EventRoomCard.vue';
</script>

<script lang="ts">
    import { defineComponent } from 'vue';
    // import EventTypes from '@/types/Events.interface';
    const axios = require('axios');

    export default defineComponent({
        name: 'ListEventRoomsApp',
        data(){
            return {
                event_rooms: null as any,
            };
        },
        mounted(){

            this.getEventRooms();
        },
        methods: {
            async getEventRooms(){

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/status/completed')
                .then((results:any) => {

                    this.event_rooms = results.data;
                })
                .catch((errors:any) => {

                    console.log(errors);
                });
            },
        }
    });
</script>