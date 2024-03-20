<template>
    <div class="flex flex-row gap-8 pt-10">
    
    <!-- <FontAwesomeIcon icon="fas fa-comments"/> -->


        
    </div>
</template>


<script setup lang="ts">
    // import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue';
    // import VActionText from '../small/VActionText.vue';
    // import VTest from '../small/VTest.vue';
    // import VPlayback from '../medium/VPlayback.vue';

    // import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
    // import { library } from '@fortawesome/fontawesome-svg-core';
    // import { faComments } from '@fortawesome/free-solid-svg-icons/faComments';

    // library.add(faComments);
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    import { notify } from 'notiwind';
    // import anime from 'animejs';
    // import VPlayback from '../medium/VPlayback.vue';
    // import { useFilteredEventsStore } from '@/stores/FilteredEventsStore';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    // import { drawCanvasRipples } from '@/helper_functions';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import { useTestStore } from '@/stores/TestStore';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                notifications: [] as any[],
                event: null as EventsAndAudioClipsTypes|null,
                is_yolo: false,
                test_store: useTestStore(),
                wtf_store: useAudioClipProcessingsStore(),

                sample_audio_clip: {
                    id: 1,
                    user: {
                        username: 'blabla',
                    },
                    audio_clip_role: {
                        id: 1,
                        audio_clip_role_name: 'originator',
                    },
                    audio_clip_tone: {
                        id: 1,
                        audio_clip_tone_name: 'happy',
                        audio_clip_tone_slug: 'happy',
                        audio_clip_tone_symbol: '🙂',
                    },
                    event_id: 1,
                    generic_status: {
                        id: 1,
                        generic_status_name: 'ok',
                    },
                    audio_file: 'https://d3cej2n7sifsea.cloudfront.net' + '/yolo/audio_ori.mp3',
                    audio_duration_s: 26,
                    audio_volume_peaks: [
                        0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2,
                        0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2
                    ],
                    is_banned: false,
                } as AudioClipsTypes,
            };
        },
        watch: {
        },
        methods: {
            async callTest() : Promise<void> {

                let data = new FormData();
                data.append('is_requesting_otp', JSON.stringify(true));

                await axios.get(window.location.origin + '/api/test', data)
                .then((result:any) => {
                    window.location.href = window.location.origin;
                    console.log(result.data);                      //native {keyA:{},keyB:"testo"}
                    console.log(result.request.status);            //number 200
                }).catch((error:any) => {
                    console.log('error at callTest()');
                    if(Object.hasOwn(error, 'request') === true && Object.hasOwn(error, 'response') === true){
                        console.log(error.response.data);               //native {keyA:{},keyB:"testo"}
                        console.log(error.request.status);              //number 418
                    }
                }).finally(()=>{
                    console.log('.finally at callTest');
                });
            },
        },
        mounted(){

            // this.callTest();

            notify({
                title: "Keep it up!",
                text: "You'll finish this project soon. You can do this!",
                type: "ok"
            }, 3000);

            window.setTimeout(()=>{
                this.is_yolo = !this.is_yolo;
            }, 2000);


        },
    });
</script>