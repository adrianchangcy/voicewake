<template>

    <!--h-20 as all relevant components will be h-20, which prevents content shifting-->
    <div class="text-theme-black h-20">

        <!--label, ripples, total duration-->
        <div
            v-show="!propIsSelected"
            ref="card_button"
            class="w-full h-full"
        >
            <VAction
                prop-element="button"
                prop-element-size="m"
                prop-font-size="m"
                :prop-is-icon-only="true"
                type="button"
                class="w-full shadow-md active:shadow-sm"
                @click.stop="handleIsSelected()"
            >
                <div class="w-full grid grid-cols-4 text-4xl">
                    <span class="sr-only">play recording</span>

                    <div class="col-span-1 h-full relative">
                        <!--total duration, width is to match emoji-->
                        <span
                            class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0 m-auto text-sm"
                        >
                            {{ prettyFileDuration }}
                        </span>
                    </div>

                    <!--ripples-->
                    <!--h-8 because VPlayback at half is h-4-->
                    <div class="col-span-2 h-8 top-0 bottom-0 my-auto relative">
                        <div
                            ref="volume_ripples_container"
                            class="w-full h-full absolute flex flex-row justify-evenly"
                        >
                            <div
                                v-for="volume_ripple in propAudioClip.audio_volume_peaks.length" :key="volume_ripple"
                                ref="volume_ripple"
                                class="h-full scale-y-0 origin-center"
                            >
                                <div class="left-0 right-0 mx-auto w-0.5 h-full bg-theme-black">
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-span-1 h-full relative">
                        <!--label-->
                        <span
                            class="w-fit h-fit absolute left-0 right-0 top-0 bottom-0.5 m-auto text-2xl has-emoji pb-0.5"
                            aria-hidden="true"
                        >
                            {{ propAudioClip.audio_clip_tone.audio_clip_tone_symbol }}
                        </span>
                        <span class="sr-only">{{ propAudioClip.audio_clip_tone.audio_clip_tone_name }}</span>
                    </div>
                </div>
            </VAction>
        </div>

        <!--for playback teleport-->
        <!--must be here to ensure it's in the correct order of focus after card_button disappears-->
        <div
            v-show="propIsSelected"
            :id="getTeleportId"
            ref="playback_container"
            class="w-full h-full"
        ></div>
    </div>
</template>


<script setup lang="ts">
    import VAction from '../small/VAction.vue';
</script>


<script lang="ts">
    import { defineComponent, PropType } from 'vue';
    import anime from 'animejs';
    import AudioClipsAndLikeDetailsTypes from '@/types/AudioClipsAndLikeDetails.interface';
    import { prettyDuration } from '@/helper_functions';


    export default defineComponent({
        data(){
            return {
                main_anime: null as InstanceType<typeof anime> | null,
            };
        },
        props: {
            propAudioClip: {
                type: Object as PropType<AudioClipsAndLikeDetailsTypes>,
                required: true,
            },
            propIsSelected: {
                type: Boolean,
                default: false
            },
        },
        computed: {
            prettyFileDuration(){

                return prettyDuration(this.propAudioClip.audio_duration_s);
            },
            getTeleportId() : string {

                return 'playback-teleport-audio-clip-id-' + this.propAudioClip.id.toString();
            },
        },
        watch: {
            propAudioClip(new_value:AudioClipsAndLikeDetailsTypes){

                this.updateAudioVolumePeaks(new_value);
            },
        },
        methods: {
            handleIsSelected() : void {

                this.$emit('isSelected', this.propAudioClip);
            },
            async handleSelectionAnime(is_selected:boolean) : Promise<void> {

                this.main_anime === null ? null : this.main_anime.pause();

                if(is_selected === true){

                    this.main_anime = anime.timeline({
                        easing: 'linear',
                        autoplay: true,
                        loop: false,
                    }).add({
                        targets: this.$refs.card_button,
                        opacity: '0',
                        duration: 0,
                        complete: () => {
                            (this.$refs.card_button as HTMLElement).style.display = 'none';
                        }
                    }).add({
                        targets: this.$refs.playback_container,
                        opacity: '1',
                        duration: 150,
                    });

                }else{

                    this.main_anime = anime.timeline({
                        easing: 'linear',
                        autoplay: true,
                        loop: false,
                    }).add({
                        targets: this.$refs.playback_container,
                        opacity: '0',
                        duration: 0,
                    }).add({
                        begin: () => {
                            (this.$refs.card_button as HTMLElement).style.display = 'grid';
                        },
                        targets: this.$refs.card_button,
                        opacity: '1',
                        duration: 150,
                    });
                }
            },
            async updateAudioVolumePeaks(new_value:AudioClipsAndLikeDetailsTypes) : Promise<void> {

                if(this.$refs.volume_ripple === undefined){

                    return;
                }

                for(let x = 0; x < new_value.audio_volume_peaks.length; x++){

                    const target_ripple = (this.$refs.volume_ripple as HTMLElement[])[x];

                    //UPDATE: non-zero feels more functional for end user
                    if(new_value.audio_volume_peaks[x] < 0.05){

                        target_ripple.style.transform = 'scaleY('+ 0.05 +')';

                    }else if(new_value.audio_volume_peaks[x] > 1){

                        target_ripple.style.transform = 'scaleY('+ 1 +')';                    

                    }else{

                        target_ripple.style.transform = 'scaleY('+ new_value.audio_volume_peaks[x] +')';                    
                    }
                }
            },
        },
        mounted(){

            this.updateAudioVolumePeaks(this.propAudioClip);
        },
    });
</script>