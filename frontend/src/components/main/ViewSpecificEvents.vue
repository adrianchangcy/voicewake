<template>
    <div class="flex flex-col gap-8">
        <div>
            <div class="py-1">
                <VPlayback
                    ref="originator_audio"
                />
            </div>
            <VLikeDislike
                :propEventId="45"
                :propLikeCount="999999"
                :propDislikeCount="1"
                :propIsLiked="null"
            />
        </div>

        <!--responders-->
        <CreateMainEvents
            :propIsOriginator="false"
            :propEventRoomId="15"
        />
    </div>
</template>


<script setup lang="ts">

    // import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VLikeDislike from '/src/components/medium/VLikeDislike.vue';
    import CreateMainEvents from '/src/components/main/CreateMainEvents.vue';

</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeDifferenceUTC } from '@/helper_functions';
    const axios = require('axios');

    export default defineComponent({
        data() {
            return {
                event_room_id: null as number|null,
                events: [],
            };
        },
        beforeMount(){
        

            const container = document.getElementsByClassName('event-room')[0];

            //change '1 Jan 2023' to '1 century ago'
            //we are passing 'YYYY-MM-DD HH:mm:ss' from template
            //for best reliability, Date() expects 'YYYY-MM-DDTHH:mm:ssZ'
            const when_created_element = container.getElementsByClassName('when-created')[0];
            const when_created = (container.getAttribute('data-when-created') as string).replace(/ /g, 'T') + 'Z';
            when_created_element.textContent = timeDifferenceUTC(new Date(when_created));

            //get event_room_id
            this.event_room_id = parseInt(container.getAttribute('data-event-room-id') as string);
        },
        mounted(){

            //get responders
            this.getResponders();
        },
        methods: {
            async getResponders(){

                if(this.event_room_id === null){

                    return;
                }

                //prepare responder events
                await axios.get('http://127.0.0.1:8000/api/events/get/by-event-room/' + this.event_room_id.toString())
                .then((results:any) => {
                    this.events = results.data;
                })
                .catch((errors:any) => {
                    console.log(errors);
                });
            },
        }
    });
</script>