<template>
    <div class="flex flex-col gap-8">

        <!--originator-->
        <div
            v-if="originator_event !== null"
        >
            <div class="w-full h-fit grid grid-cols-8 gap-2">
                <div class="col-span-6">
                    <VPlayback
                        :propAudioVolumePeaks="originator_event.audio_volume_peaks"
                        :propBucketQuantity="originator_event.audio_volume_peaks.length"
                        :propAudioURL="originator_event.audio_file"
                    />
                </div>
                <div class="col-span-2 relative border border-theme-light-gray rounded-lg">
                    <span class="text-3xl w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">{{ originator_event.event_tone.event_tone_symbol }}</span>
                </div>
            </div>
            <div class="w-full h-fit grid grid-cols-8 pt-2">
                <VLikeDislike
                    :propEventId="originator_event.id"
                    :propLikeCount="originator_event.like_count"
                    :propDislikeCount="originator_event.dislike_count"
                    :propIsLiked="originator_event.is_liked_by_user"
                    class="col-span-6 lg:col-span-5"
                />
            </div>
        </div>

        <!--responders-->
        <div
            v-for="event in responder_events" :key="event.id"
        >
            <VUser
                :propUsername="event.user_event_role.user.username"
            />
            <div class="w-full h-fit grid grid-cols-8 gap-2">
                <div class="col-span-6">
                    <VPlayback
                        :propAudioVolumePeaks="event.audio_volume_peaks"
                        :propBucketQuantity="event.audio_volume_peaks.length"
                        :propAudioURL="event.audio_file"
                    />
                </div>
                <div class="col-span-2 relative border border-theme-light-gray rounded-lg">
                    <span class="text-3xl w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto">{{ event.event_tone.event_tone_symbol }}</span>
                </div>
            </div>
            <div class="w-full h-fit grid grid-cols-8 pt-2">
                <VLikeDislike
                    :propEventId="event.id"
                    :propLikeCount="event.like_count"
                    :propDislikeCount="event.dislike_count"
                    :propIsLiked="event.is_liked_by_user"
                    class="col-span-6 lg:col-span-5"
                />
            </div>
        </div>

        <!--reply-->
        <VCreateEvents
            :propIsOriginator="false"
            :propEventRoomId="event_room_id"
        />
    </div>
</template>


<script setup lang="ts">

    // import VSectionTitle from '/src/components/small/VSectionTitle.vue';
    import VPlayback from '/src/components/medium/VPlayback.vue';
    import VLikeDislike from '/src/components/medium/VLikeDislike.vue';
    import VCreateEvents from '/src/components/medium/VCreateEvents.vue';
    import VUser from '/src/components/small/VUser.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { timeDifferenceUTC } from '@/helper_functions';
    import EventTypes from '@/types/Events.interface';
    const axios = require('axios');

    export default defineComponent({
        name: 'GetEventRoomsApp',
        data() {
            return {
                event_room_id: null as number|null,
                originator_event: null as EventTypes|null,
                responder_events: [] as EventTypes[],
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
            this.getEvents();
        },
        methods: {
            async getEvents(){

                if(this.event_room_id === null){

                    return;
                }

                //prepare events, then separate
                await axios.get('http://127.0.0.1:8000/api/events/get/event-room/' + this.event_room_id.toString())
                .then((results:any) => {

                    //separate originator from responder
                    //doing it via loop, instead of relying on [0] being originator, helps us guarantee our event placements
                    for(let x=0; x < results.data.length; x++){

                        if((results.data[x] as EventTypes).user_event_role.event_role.event_role_name === 'originator'){

                            this.originator_event = results.data[x];

                        }else{

                            this.responder_events.push(results.data[x]);
                        }
                    }
                })
                .catch((errors:any) => {

                    console.log(errors);
                });
            },
        }
    });
</script>