<template>
    <div class="flex flex-row gap-8 pt-20">
    <!-- <FontAwesomeIcon icon="fas fa-comments"/> -->





















        <!--BLANK STATE, DON'T MODIFY THIS -->
        <!--light mode, -->
        <div v-show="false" class="w-full bg-theme-light flex flex-col gap-6">

            <!--normal-->
            <div class="flex flex-col mx-auto">
                <span class="mx-auto">normal</span>
                <button
                    type="button"
                    class="w-20 h-20 flex items-center border-t-2 rounded-lg shadow-lg"
                >
                    <span class="mx-auto pb-0.5 text-xl font-medium">
                        Teapot
                    </span>
                </button>
            </div>

            <!--hover-->
            <div class="flex flex-col mx-auto">
                <span class="mx-auto">hover</span>
                <button
                    type="button"
                    class="w-20 h-20 flex items-center border-t-2 rounded-lg shadow-lg"
                >
                    <span class="mx-auto pb-0.5 text-xl font-medium">
                        Teapot
                    </span>
                </button>
            </div>

            <!--active (clicked)-->
            <div class="flex flex-col mx-auto">
                <span class="mx-auto">active</span>
                <button
                    type="button"
                    class="w-20 h-20 flex items-center border-t-2 rounded-lg shadow-lg"
                >
                    <span class="mx-auto pb-0.5 text-xl font-medium">
                        Teapot
                    </span>
                </button>
            </div>

            <!--disable-->
            <div class="flex flex-col mx-auto">
                <span class="mx-auto">disable</span>
                <button
                    type="button"
                    class="w-20 h-20 flex items-center border-t-2 rounded-lg shadow-lg"
                >
                    <span class="mx-auto pb-0.5 text-xl font-medium">
                        Teapot
                    </span>
                </button>
            </div>
        </div>





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
    // import { notify } from '@/wrappers/notify_wrapper';
    // import anime from 'animejs';
    // import VPlayback from '../medium/VPlayback.vue';
    // import { useFilteredEventsStore } from '@/stores/FilteredEventsStore';
    import { useAudioClipProcessingsStore } from '@/stores/AudioClipProcessingsStore';
    import EventsAndAudioClipsTypes from '@/types/EventsAndAudioClips.interface';
    // import { getShortenedString } from '@/helper_functions';
    import AudioClipsTypes from '@/types/AudioClips.interface';
    import { useTestStore } from '@/stores/TestStore';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                test_store: useTestStore(),
                audio_clip_processings_store: useAudioClipProcessingsStore(),

                notifications: [] as any[],
                event: null as EventsAndAudioClipsTypes|null,
                is_yolo: false,

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

            // notify({
            //     title: 'Keep it up!',
            //     text: "You're so close to the finish line! Keep going!!!",
            //     type: 'ok',
            //     icon: {'font_awesome': 'fas fa-check'},
            // }, -1);

            // window.setInterval(()=>{
            //     this.is_yolo = !this.is_yolo;
            // }, 2000);






        },
    });
</script>