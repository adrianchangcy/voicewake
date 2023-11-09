<template>
    <div class="flex flex-col gap-8 pt-10">











    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    // import VActionTextOnly from '../small/VActionTextOnly.vue';
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    // import anime from 'animejs';
    // import VPlayback from '../medium/VPlayback.vue';
    // import { useFilteredEventsStore } from '@/stores/FilteredEventsStore';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                notifications: [] as any[],
                event: null as EventsAndAudioClipsTypes|null,
            };
        },
        watch: {
        },
        methods: {
            async callTest() : Promise<void> {

                let data = new FormData();
                data.append('email', 'user1@gmail.com');
                data.append('is_requesting_otp', JSON.stringify(true));

                await axios.get(window.location.origin + '/api/test', data)
                .then((result:any) => {
                    console.log(result.data);                      //native {data:{},message:"testo"}
                    console.log(result.request.status);            //number 200
                }).catch((error:any) => {
                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){
                        console.log(error.response.data);               //native {data:{},message:"testo"}
                        console.log(error.request.status);              //number 418
                    }
                });
            },
            async getEvent(event_id:number) : Promise<void> {

                //prepare audio_clips, then separate
                await axios.get(window.location.origin + '/api/audio_clips/get/event/' + event_id.toString())
                .then((result:any) => {

                    if(result.data['data'].length === 0){

                        return;
                    }

                    //API always returns list, even if there is only one event
                    this.event = result.data['data'][0];
                })
                .catch((error:any) => {

                    let error_text = '';

                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){

                        error_text = error.response.data['message'];
                    }

                    notify({
                        title: "AudioClip search failed",
                        text: error_text,
                        type: "error"
                    }, 3000);
                });
            },
        },
        mounted(){

            this.callTest();

            notify({
                title: "Keep it up!",
                text: "You'll finish this project soon. You can do this!",
                type: "ok"
            }, 3000);

            let yolo = {'ho': 1};
            console.log(Object.hasOwn(yolo, 'ho'));
            console.log('ho' in yolo);
            console.log(Object.hasOwn(Object.keys(yolo), 'ho'));
        },
    });
</script>