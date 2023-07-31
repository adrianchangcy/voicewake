<template>
    <div>

        <!--testing multiple VPlayback tracking-->
        <div v-if="event_room !== null">
            <VPlayback
                :propAudioVolumePeaks="event_room.originator!.audio_volume_peaks"
                :propBucketQuantity="event_room.originator!.audio_volume_peaks.length"
                :propAudioURL="event_room.originator!.audio_file"
                :propEventTone="event_room.originator!.event_tone"
                :propRecordToStoreOnSourceChange="true"
            />
            <VPlayback
                :propAudioVolumePeaks="event_room.originator!.audio_volume_peaks"
                :propBucketQuantity="event_room.originator!.audio_volume_peaks.length"
                :propAudioURL="event_room.originator!.audio_file"
                :propEventTone="event_room.originator!.event_tone"
                :propRecordToStoreOnSourceChange="true"
            />
        </div>

    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    // import anime from 'animejs';
    import VPlayback from '../medium/VPlayback.vue';
    import EventRoomTypes from '@/types/EventRooms.interface';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                notifications: [] as any[],
                event_room: null as EventRoomTypes|null,
            };
        },
        methods: {
            async getEventRoom(event_room_id:number) : Promise<void> {

                //prepare events, then separate
                await axios.get(window.location.origin + '/api/events/get/event-room/' + event_room_id.toString())
                .then((results:any) => {

                    if(results.data['data'].length === 0){

                        return;
                    }

                    //API always returns list, even if there is only one event_room
                    this.event_room = results.data['data'][0];
                })
                .catch((error:any) => {

                    notify({
                        title: "Event search failed",
                        text: error.response.data['message'],
                        type: "error"
                    }, 3000);
                });
            },
            axiosSetup() : boolean {

                //your template must have {% csrf_token %}
                const token = document.getElementsByName("csrfmiddlewaretoken")[0];

                if(token === undefined){

                    console.log('CSRF not found.');
                    return false;
                }

                axios.defaults.headers.common['X-CSRFToken'] = (token as HTMLFormElement).value;
                axios.defaults.headers.post['Content-Type'] = 'multipart/form-data';
                return true;
            },
        },

        mounted(){

            this.axiosSetup();
            this.getEventRoom(2);




            notify({
                title: "Keep it up!",
                text: "You'll finish this project soon. You can do this!",
                type: "ok"
            }, 3000);
        },
    });
</script>