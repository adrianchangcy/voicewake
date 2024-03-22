<template>
    <!--pass pb-__ here to customise/prevent emoji overflow-->
    <div class="w-full h-full">

        <!--on overflow, it overflows to the right while never going past left side-->
        <!--so pr-10 is ensuring that it doesn't go too far to the right-->
        <!--our audio_clip_tone_elements being absolute helps auto-adjust-->
        <div
            ref="audio_clip_tones_container"
            class="h-full flex flex-row justify-between pl-5 pr-10 overflow-x-clip"
        >

            <!--must use quantity_used so that elements and their ref is already defined and available-->
            <!--FYI, v-for when using with number, starts from 1-->
            <div
                v-for="n in quantity_used"
                :key="n"
                class="flex-1 h-full relative"
            >

                <!--need ? else we get undefined, since this v-for starts before API call-->
                <!--using v-if outside v-for did not fix the issue-->
                <!--must also use absolute, as audio_clip_tones have different sizes, causing shifting otherwise-->
                <span
                    ref="audio_clip_tones_elements"
                    aria-hidden="true"
                    class="text-base w-fit h-fit block absolute left-0 right-0 top-0 m-auto select-none"
                    style="opacity: 0;"
                >
                    {{ audio_clip_tones[randomised_audio_clip_tones_indexes[n - 1]]?.audio_clip_tone_symbol }}
                </span>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
</script>


<script lang="ts">
    import { defineComponent } from 'vue';
    // import { notify } from '@/wrappers/notify_wrapper';
    import anime from 'animejs';
    // import VPlayback from '../medium/VPlayback.vue';
    import AudioClipTonesTypes from '@/types/AudioClipTones.interface';
    import { getRandomNumber } from '@/helper_functions';
    const axios = require('axios');

    export default defineComponent({
        data(){
            return {
                audio_clip_tones: [] as AudioClipTonesTypes[],
                randomised_audio_clip_tones_indexes: [] as number[],
                quantity_used: 20,
            };
        },
        methods: {
            async getAudioClipTones() : Promise<void> {

                await axios.get(window.location.origin + '/api/audio-clips/tones/list')
                .then((result:any) => {

                    //get our audio_clip_tones
                    //wasn't able to store audio_clip_tone_symbol directly here in this file, so we do this
                    //ensures we use accurate emojis too, since our audio_clip_tones in db are after skimming
                    if(result.data['data'].length < this.quantity_used){

                        throw new Error(
                            'Expected ' + this.quantity_used.toString() + ' audio_clip_tones, got ' +
                            result.data['data'].length.toString() + '.'
                        );
                    }

                    this.audio_clip_tones = result.data['data'];

                }).then(() => {

                    //pre-fill first
                    for(let x=0; x < this.quantity_used; x++){

                        //random array index
                        this.randomised_audio_clip_tones_indexes.push(
                            Math.floor(getRandomNumber(0, this.audio_clip_tones.length))
                        );
                    }

                    //start anime
                    this.startAnime();

                }).catch(()=>{

                    //fail silently, since this component is not important
                });
            },
            async startAnime() : Promise<void> {

                if(this.randomised_audio_clip_tones_indexes.length < this.quantity_used){

                    return;
                }

                //get height
                //does not change on zoom
                const y_px = (this.$refs.audio_clip_tones_container as HTMLElement).getBoundingClientRect().height;

                //minimum distance to travel
                //if too little, it will look stuttery
                const minimum_translate_y_distance = Math.floor(y_px * 0.75);

                //maximum start, to guarantee minimum distance
                const maximum_translate_y_start = y_px - minimum_translate_y_distance;

                //kickstart the anime
                for(let x=0; x < this.quantity_used; x++){

                    //can start anywhere, but with limit
                    // const random_translate_y_start = Math.floor(getRandomNumber(0, translate_y_start_limit));

                    //ensure that we get good distance, else it stutters when too short
                    // const random_translate_y_end = Math.floor(getRandomNumber(random_translate_y_start, y_px));

                    //get our values
                    //we can also use shorter duration to prevent stuttering
                    const random_delay = Math.floor(getRandomNumber(0, 6000));
                    const random_duration = Math.floor(getRandomNumber(1500, 3500));
                    const translate_y_start = Math.floor(getRandomNumber(0, maximum_translate_y_start));
                    const translate_y_end = Math.floor(getRandomNumber((translate_y_start + minimum_translate_y_distance), y_px));

                    //set random scale
                    (this.$refs.audio_clip_tones_elements as HTMLElement[])[x].style.transform =
                        'scale(' + getRandomNumber(1, 1.5).toString() + ')';

                    //use completed as sort of an infinite loop
                    //we specify more opacity values so we can reach 0 to 1 as early as possible
                    //otherwise, reaching opacity 1 too slowly causes undesired gap above
                    anime({
                        targets: (this.$refs.audio_clip_tones_elements as HTMLElement[])[x],
                        translateY: [translate_y_start.toString() + 'px', translate_y_end.toString() + 'px'],
                        opacity: ['0', '1', '0.6', '0.4', '0.2', '0'],
                        delay: random_delay,
                        easing: 'linear',
                        autoplay: true,
                        duration: random_duration,
                        loop: true,
                        loopComplete: ()=>{

                            //replace audio_clip_tone_symbol randomly
                            this.randomised_audio_clip_tones_indexes[x] = Math.floor(getRandomNumber(0, this.audio_clip_tones.length));
                        }
                    });
                }

            },
        },
        mounted(){

            this.getAudioClipTones();



        },
    });
</script>