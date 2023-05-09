<template>
    <div>
        <div v-if="event_room !== null">
            <EventRoomCard
                :propEventRoom="event_room"
                :propShowTitle="false"
                :propShowOnePlaybackPerEvent="event_room.responder.length === 0"
                :propShowReplyMenu="true"
                :propIsInContainer="false"
            />
        </div>
    </div>
</template>


<script setup lang="ts">
    import EventRoomCard from '@/components/main/EventRoomCard.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeDifferenceUTC } from '@/helper_functions';
    import EventRoomTypes from '@/types/EventRooms.interface';
    const axios = require('axios');

    export default defineComponent({
        name: 'GetEventRoomsApp',
        data() {
            return {
                event_room_id: null as number|null,
                event_room: null as EventRoomTypes|null,
            };
        },
        beforeMount(){
        
            const container = document.getElementsByClassName('event-room')[0];

            //get event_room_id
            this.event_room_id = parseInt(container.getAttribute('data-event-room-id') as string);

            //check for empty element, e.g. when deleted
            if(container.getElementsByClassName('when-created').length === 0){

                return;
            }

            //change '1 Jan 2023' to '1 century ago'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            const when_created_element = container.getElementsByClassName('when-created')[0];
            const when_created = (container.getAttribute('data-when-created') as string).replace(/ /g, 'T') + 'Z';
            when_created_element.textContent = timeDifferenceUTC(new Date(when_created));
        },
        mounted(){

            //get responders
            this.getEventRoom();
        },
        methods: {
            async getEventRoom(){

                if(this.event_room_id === null){

                    return;
                }

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/event-room/' + this.event_room_id.toString())
                .then((results:any) => {

                    if(results.data.length > 0){

                        this.event_room = results.data[0];
                    }
                })
                .catch((errors:any) => {

                    console.log(errors);
                });
            },
        }
    });
</script>